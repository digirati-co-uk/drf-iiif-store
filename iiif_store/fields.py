import logging
from rest_framework import serializers

logger = logging.getLogger(__name__)


IIIF_3 = "http://iiif.io/api/presentation/3/context.json"
IIIF_2 = "http://iiif.io/api/presentation/2/context.json"
UNKNOWN = "Unknown"


class IIIFPresentationVersionField(serializers.CharField):
    """Determines the version of the IIIF presentation spec being used
    in the provided iiif resource.
    """

    def to_representation(self, iiif_resource):
        if context := iiif_resource.get("@context"):
            return context
        if iiif_resource.get("@id") and iiif_resource.get("@type"):
            return IIIF_2
        if iiif_resource.get("id") and iiif_resource.get("type"):
            return IIIF_3
        return UNKNOWN


class IIIFPresentationTypeField(serializers.CharField):
    """Version-agnostic retrieval of the resource type of a provided
    IIIF Presentation resource."""

    def to_representation(self, iiif_resource):
        if iiif3_type := iiif_resource.get("type"):
            return iiif3_type
        elif iiif2_type := iiif_resource.get("@type"):
            namespace, iiif_type = iiif2_type.split(":")
            return iiif_type
        return UNKNOWN


class IIIFImageResourceField(serializers.CharField):
    """Version-agnostic retrieval of the primary image resource of a
    provided IIIF Presentation resource.
    """

    def get_first_iiif3_image(self, iiif_resource):
        """Recursively traverse iiif3 until the first
        image resource is encountered.
        """
        image_resource = None
        if image_body := iiif_resource.get("body"):
            image_resource = image_body
        else:
            for iiif_element in iiif_resource.get("items", []):
                if image := self.get_first_iiif3_image(iiif_element):
                    image_resource = image
        return image_resource

    def image_from_iiif2_canvas(self, iiif2_canvas):
        image_resource = None
        for image in iiif2_canvas.get("images", []):
            if image_resource := image.get("resource"):
                return image_resource
        return image_resource

    def image_from_iiif2_sequence(self, iiif2_sequence, target_id=""):
        """Return an image resource from the provided iiif2_sequence,
        either that identified by the target_id passed in,
        the startCanvas attribute on the sequence,
        or the first image resource to be found.

        """
        image_resource = None
        if (start_canvas := iiif2_sequence.get("startCanvas")) and not target_id:
            target_id = start_canvas

        if target_id:
            # Attempt to get the image resource of the targeted canvas.
            for iiif2_canvas in iiif2_sequence.get("canvases", []):
                if iiif2_canvas.get("@id") == target_id:
                    image_resource = self.image_from_iiif2_canvas(iiif2_canvas)
            if image_resource:
                return image_resource
        # Otherwise fall back on the first image resource in the sequence.
        for iiif2_canvas in iiif2_sequence.get("canvases", []):
            image_resource = self.image_from_iiif2_canvas(iiif2_canvas)
            if image_resource:
                return image_resource
        return image_resource

    def get_first_iiif2_image(self, iiif_resource):
        for sequence in iiif_resource.get("sequences", []):
            if image_resource := self.image_from_iiif2_sequence(sequence):
                return image_resource
        return None

    def to_representation(self, iiif_resource):
        if iiif_resource.get("items"):
            return self.get_first_iiif3_image(iiif_resource)
        elif iiif_resource.get("sequences"):
            return self.get_first_iiif2_image(iiif_resource)
        elif iiif_resource.get("images"):
            return self.image_from_iiif2_canvas(iiif_resource)
        return {}


class IIIFManifestCanvasesField(serializers.Serializer):
    """Version-agnostic retrieval of all canvases in a IIIF Manifest."""

    def to_representation(self, iiif_resource):
        if sequences := iiif_resource.get("sequences"):
            return [canvas for seq in sequences for canvas in seq.get("canvases")]
        if items := iiif_resource.get("items"):
            return items

        # TODO: Add structures
        else:
            return []


class IIIFThumbnailResourceField(IIIFImageResourceField):
    """Version-agnostic retrieval of the thumbnail image resource for a
    a IIIF Resource, either from the thumbnail property, or the primary image resource."""

    def to_representation(self, iiif_resource):
        thumbnail_resource = {}
        if thumbnail := iiif_resource.get("thumbnail"):
            thumbnail_resource = thumbnail
        if not thumbnail_resource:
            thumbnail_resource = super().to_representation(iiif_resource)
        if isinstance(thumbnail_resource, list):
            return thumbnail_resource[0]
        return thumbnail_resource


class IIIFImageURLMixin:
    def to_representation(self, iiif_resource):
        image_url = ""
        resource = super().to_representation(iiif_resource)
        if iiif3_id := resource.get("id"):
            image_url = iiif3_id
        elif iiif2_id := resource.get("@id"):
            image_url = iiif2_id
        return image_url


class IIIFImageURLField(IIIFImageURLMixin, IIIFImageResourceField):
    pass


class IIIFThumbnailURLField(IIIFImageURLMixin, IIIFThumbnailResourceField):
    pass
