import logging
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.contenttypes.models import ContentType

from search_service.serializers import (
    BaseModelToIndexableSerializer,
)

from search_service.models import ResourceRelationship

from .models import (
    IIIFResource,
)

logger = logging.getLogger(__name__)


class IIIFResourceCreateSerializer(serializers.ModelSerializer):
    iiif_type = serializers.CharField(required=False)
    original_id = serializers.CharField(
        required=False,
    )
    thumbnail = serializers.JSONField(required=False)
    label = serializers.JSONField(required=False)

    def to_internal_value(self, data):
        original_id = data.get("iiif_json", {}).get("id", "")
        if not original_id:
            original_id = data.get("iiif_json", {}).get("@id", "")
        data["iiif_type"] = data.get("iiif_json", {}).get("type", "").lower()
        data["original_id"] = original_id
        data["thumbnail"] = data.get("iiif_json", {}).get("thumbnail", {})
        data["label"] = data.get("iiif_json", {}).get("label", {})
        return super().to_internal_value(data)

    def save(self, **kwargs):
        """This will act as a create or update for IIIFResources, using the original id as
        a unique identifier for IIIFResource objects.
        """
        if self.instance is None:
            original_id = self.validated_data.get("original_id", "")
            logger.debug(
                f"No instance supplied, looking for existing IIIFResources: ({original_id})"
            )
            try:
                existing_resource = IIIFResource.objects.get(original_id=original_id)
                if existing_resource:
                    logger.debug(
                        f"Using existing IIIFResource as instance: ({original_id}, {existing_resource.id})"
                    )
                    self.instance = existing_resource
            except IIIFResource.DoesNotExist:
                logger.debug(f"No existing IIIFResource: ({original_id})")
        return super().save(**kwargs)

    class Meta:
        model = IIIFResource
        fields = [
            "id",
            "iiif_type",
            "original_id",
            "label",
            "thumbnail",
            "iiif_json",
        ]


class IIIFResourceRelationshipCreateSerializer(serializers.ModelSerializer):
    def to_internal_value(self, data):
        source_resource = IIIFResource.objects.get(original_id=data.get("source"))
        target_resource = IIIFResource.objects.get(original_id=data.get("target"))
        relationship_type = data.get("type", "isPartOf")
        return {
            "source_id": source_resource.id,
            "source_content_type": ContentType.objects.get_for_model(
                source_resource
            ),
            "target_id": target_resource.id,
            "target_content_type": ContentType.objects.get_for_model(
                target_resource
            ),
            "type": relationship_type,
        }

    class Meta:
        model = ResourceRelationship
        fields = "__all__"


class SourceIIIFToIIIFResourcesSerializer(serializers.Serializer):
    """Extract all distinct IIIF elements from a IIIF resource (e.g. a Manifest),
    along with `ispartof` relationship between the original iiif ids.
    """

    def get_distinct_iiif_elements_and_relationships(self, iiif_element, parent_ids=[]):
        resource_id = iiif_element.get("id")
        relationships = [
            {
                "target": parent_id,
                "source": resource_id,
            }
            for parent_id in parent_ids
        ]
        child_parent_ids = [resource_id] + parent_ids
        resources = [{"iiif_json": iiif_element}]
        if items := iiif_element.get("items"):
            for i in items:
                res, rels = self.get_distinct_iiif_elements_and_relationships(
                    i, child_parent_ids
                )
                resources.extend(res)
                relationships.extend(rels)
        return resources, relationships

    def to_internal_value(self, data):
        resources, relationships = self.get_distinct_iiif_elements_and_relationships(
            data.get("iiif_json")
        )
        return {
            "resources": resources,
            "relationships": relationships,
        }

    def create(self, validated_data):
        resource_serializer = IIIFResourceCreateSerializer(
            data=validated_data.get("resources"), many=True
        )
        resource_serializer.is_valid(raise_exception=True)
        resource_serializer.save()

        relationship_serializer = IIIFResourceRelationshipCreateSerializer(
            data=validated_data.get("relationships"), many=True
        )
        relationship_serializer.is_valid(raise_exception=True)
        relationship_serializer.save()

        return resource_serializer.data


class IIIFSummarySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = IIIFResource
        fields = [
            "url",
            "iiif_type",
            "label",
            "thumbnail",
        ]
        extra_kwargs = {
            "url": {
                "view_name": "iiif_store:iiifresource-detail",
                "lookup_field": "id",
            }
        }


class IIIFSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return instance.iiif_json

    class Meta:
        model = IIIFResource
        fields = ["iiif_json"]


class IIIFResourceSummarySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = IIIFResource
        fields = [
            "url",
            "id",
            "iiif_type",
            "created",
            "modified",
            "original_id",
            "label",
            "thumbnail",
        ]
        extra_kwargs = {
            "url": {
                "view_name": "api:iiif_store:iiifresource-detail",
                "lookup_field": "id",
            }
        }


class IIIFResourceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = IIIFResource
        fields = [
            "url",
            "id",
            "iiif_type",
            "original_id",
            "label",
            "thumbnail",
            "iiif_json",
        ]
        extra_kwargs = {
            "url": {
                "view_name": "api:iiif_store:iiifresource-detail",
                "lookup_field": "id",
            }
        }


class IIIFResourceToIndexableSerializer(BaseModelToIndexableSerializer):
    def to_indexables(self, instance):
        return [
            {
                "type": "descriptive",
                "subtype": "label",
                "original_content": instance.original_id,
                "indexable_text": instance.original_id,
            }
        ]
