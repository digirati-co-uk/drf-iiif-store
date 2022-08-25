import logging
from rest_framework import serializers

logger = logging.getLogger(__name__)


class IIIFImageURLField(serializers.JSONField):
    """Gets the primary image url of a IIIF Resource."""

    def get_image_body(self, iiif_element):
        return iiif_element.get("body")

    def get_first_image(self, iiif_resource):
        if image_body := self.get_image_body(iiif_resource):
            return image_body
        else:
            for iiif_element in iiif_resource.get("items", []):
                if image := self.get_first_image(iiif_element):
                    return image
            return None

    def to_representation(self, iiif_resource):
        if image := self.get_first_image(iiif_resource):
            return image.get("id")
        return ""


class IIIFThumbnailURLField(IIIFImageURLField):
    """Gets the primary thumbnail url of a IIIF Resource."""

    pass
