import json
import requests
import logging

from .serializer_utils import (
    resources_by_type,
)

logger = logging.getLogger(__name__)


def get_first_canvas(iiif_resource, manifest=None):
    """Gets the first canvas for a IIIF resource, the parent manifest must be provided
    if the resource is a range.
    """
    iiif_type = iiif_resource.get("type")
    first_canvas_json = None
    if iiif_type == "Range":
        # This is a range, so we need to do something different to get the first canvas json
        # Get the JSON from the item list in the Range itself.
        range_first_canvas_json = next(
            iter(resources_by_type(iiif=iiif_resource, iiif_type=("Canvas", "SpecificResource"))),
            None,
        )
        # Remove any hash fragment if there is one.
        if (canvas_identifier := range_first_canvas_json.get("id", range_first_canvas_json.get("source", None))) is not None:
            canvas_identifier = canvas_identifier.split("#")[0]
            # Get the canvases from the parent manifest
            if manifest:
                canvases = resources_by_type(iiif=manifest)
            else:
                canvases = None
            # Now we try to get the first canvas from the manifest items where that canvas has the ID for the
            # first canvas in the range
            if canvases and canvas_identifier:
                first_canvas_json = next(
                    iter([x for x in canvases if x["id"] == canvas_identifier]), None
                )
    elif iiif_type == "Canvas":
        first_canvas_json = iiif_resource
    else:
        first_canvas_json = next(iter(resources_by_type(iiif=iiif_resource)), None)
    return first_canvas_json


def get_info_json_data(image_service_id):
    info_url = f"{image_service_id}/info.json"
    logger.debug(f"Fetching info.json: ({info_url})")
    try:
        info = requests.get(info_url)
        return info.json()
    except (requests.exceptions.HTTPError, json.decoder.JSONDecodeError) as e:
        logger.warning("Could not fetch info.json: ({info_url}, {e})")
        return {}


def get_image_services(content_resource):
    """Given a IIIF Presentation API 3 content resource, return the image services
    labelled as a iiif2 or iiif3 image service, with empty values if not found.
    """
    services = content_resource.get("service", [])
    iiif2 = next(
        iter(
            [
                x
                for x in services
                if ("http://iiif.io/api/image/2" in x.get("profile"))
                or (x.get("@type") == "ImageService2") or (x.get("type") == "ImageService2")
            ]
        ),
        {},
    )
    iiif3 = next(iter([x for x in services if x.get("type") == "ImageService3"]), {})
    return {"ImageService3": iiif3, "ImageService2": iiif2}


def normalise_thumbnail_services(thumbnail_json):
    """Attempts to fetch and add the info.json to thumbnail services so that
    thumbnail urls can be generated using fixed size values, or on the basis of other
    image service properties.
    """
    image_services = get_image_services(thumbnail_json)
    normalised_image_services = []
    for i_s in image_services.values():
        if not (i_s_id := i_s.get("id")):
            i_s_id = i_s.get("@id")
        if i_s_id:
            info_json = get_info_json_data(i_s_id)
            i_s["info"] = info_json
            normalised_image_services.append(i_s)
    if not normalised_image_services:
        # TODO fallback to service id from thumbnail url if IIIF
        logger.debug(f"No image services found in thumbnail_json: ({thumbnail_json})")
        logger.debug(f"Image services from get_image_services {image_services}")
    thumbnail_json["service"] = normalised_image_services
    return thumbnail_json


def get_iiif_resource_thumbnail_json(iiif_resource, first_canvas_json={},
                                     fallback=False):
    """Defaults to using the thumbnail property that has been set for the
    iiif resource, but if this is absent it will attempt to extract a thumbnail
    from the first canvas (or the first canvas' descendent objects) following
    the logic described in:
        https://github.com/atlas-viewer/iiif-image-api/blob/master/src/README.md
    """
    thumbnail_json = iiif_resource.get("thumbnail", [])
    logger.debug(f"IIIF id passed to thumbnail code: {iiif_resource.get('id', iiif_resource.get('@id', None))}")
    if not thumbnail_json and first_canvas_json:
        logger.debug("No thumbnail block on the resource")
        if annotations := resources_by_type(iiif=first_canvas_json, iiif_type="Annotation"):
            image_annotation_bodies = [
                a.get("body")
                for a in annotations
                if a.get("motivation") == "painting" and a["body"].get("type") == "Image"
            ]
            if image_annotation_bodies:
                thumbnail_json = image_annotation_bodies[:1]
    if fallback:
        logger.debug("Dereferencing the info.json for the thumbnail")
        try:
            thumbnail_json = [normalise_thumbnail_services(thumbnail) for thumbnail in thumbnail_json]
        except requests.exceptions.ConnectionError:
            thumbnail_json = None
    # else:
    #     thumbnail_json = None
    if not thumbnail_json:
        logger.debug(f'No potential thumbnails found for iiif resource: ({iiif_resource.get("id")})')
        logger.debug(f'Thumbnail json in empty thumbnail: {thumbnail_json}')
        return
    return thumbnail_json


def format_thumbnail_url(thumbnail_json):
    """Formats a default thumbnail url to populate madoc_thumbnail"""
    if services := thumbnail_json[0].get("service"):
        if info := services[0].get("info"):
            thumbnail_id = info.get("@id")
        else:
            thumbnail_id = services[0].get("@id", services[0].get("id"))
    else:
        thumbnail_id = thumbnail_json[0].get("id")
    return f"{thumbnail_id}/full/400,/0/default.jpg"
