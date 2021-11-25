import logging
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import (
    StoredIIIFResource,
)

logger = logging.getLogger(__name__)


class IIIFSerializer(serializers.HyperlinkedModelSerializer):
    def to_representation(self, instance):
        return instance.iiif_json

    class Meta:
        model = StoredIIIFResource
        fields = ["iiif_json"]


class StoredIIIFResourceSerializer(serializers.HyperlinkedModelSerializer):
    original_id = serializers.CharField(
        required=False, validators=[UniqueValidator(queryset=StoredIIIFResource.objects.all())]
    )
    thumbnail = serializers.JSONField(required=False)
    label = serializers.JSONField(required=False)

    def is_valid(self, **kwargs):
        original_id = self.initial_data.get("iiif_json", {}).get("id", "")
        if not original_id:
            original_id = self.initial_data.get("iiif_json", {}).get("@id", "")
        self.initial_data["iiif_type"] = self.initial_data.get("iiif_type", "").lower()
        self.initial_data["original_id"] = original_id
        self.initial_data["thumbnail"] = self.initial_data.get("iiif_json", {}).get(
            "thumbnail", {}
        )
        self.initial_data["label"] = self.initial_data.get("iiif_json", {}).get("label", {})
        return super().is_valid(**kwargs)

    def save(self, **kwargs):
        """This will act as a create or update for StoredIIIFResources, using the original id as
        a unique identifier for StoredIIIFResource objects.
        """
        if self.instance is None:
            original_id = self.validated_data.get("original_id", "")
            logger.debug(
                f"No instance supplied, looking for existing StoredIIIFResources: ({original_id})"
            )
            try:
                existing_resource = StoredIIIFResource.objects.get(original_id=original_id)
                if existing_resource:
                    logger.debug(
                        f"Using existing StoredIIIFResource as instance: ({original_id}, {existing_resource.id})"
                    )
                    self.instance = existing_resource
            except StoredIIIFResource.DoesNotExist:
                logger.debug(f"No existing StoredIIIFResource: ({original_id})")
        return super().save(**kwargs)

    class Meta:
        model = StoredIIIFResource
        fields = [
            "id",
            "iiif_type",
            "original_id",
            "label",
            "thumbnail",
            "iiif_json",
        ]
