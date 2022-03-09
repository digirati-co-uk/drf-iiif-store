import logging
import copy
import bleach
import json 
from bs4 import BeautifulSoup
import dateutil.parser
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import get_language

from search_service.serializers import (
    BaseModelToIndexableSerializer,
)

from search_service.models import ResourceRelationship

from .models import (
    IIIFResource,
)
from .settings import iiif_store_settings

default_lang = get_language()

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
            "source_content_type": ContentType.objects.get_for_model(source_resource),
            "target_id": target_resource.id,
            "target_content_type": ContentType.objects.get_for_model(target_resource),
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
        if iiif_element.get("type") in iiif_store_settings.IIIF_RESOURCE_TYPES: 
            resource_id = iiif_element.get("id")
            relationships = [
                {
                    "target": parent_id,
                    "source": resource_id,
                }
                for parent_id in parent_ids
            ]
            child_parent_ids = [resource_id] + parent_ids
            resources = [{"iiif_json": copy.deepcopy(iiif_element)}]
        else:
            relationships = []
            resources = []
            child_parent_ids = [] + parent_ids
        if items := iiif_element.get("items"):
            for i in items:
                res, rels = self.get_distinct_iiif_elements_and_relationships(
                    i, child_parent_ids
                )
                resources.extend(res)
                relationships.extend(rels)
        return resources, relationships

    def update_parent_resources_with_child_resource_ids(self, relationships): 
        """
            """
        parent_data = {rel.target_id: str(rel.target.iiif_json) for rel in relationships} 
        for rel in relationships: 
            parent_data[rel.target_id] = parent_data[rel.target_id].replace(
                    rel.source.original_id, rel.source.iiif_json.get("id")
                    )
        for parent_id, parent_iiif_json_str in parent_data.items(): 
            parent_resource = IIIFResource.objects.get(id=parent_id)
            parent_resource.iiif_json = json.loads(parent_iiif_json_str)
            parent_resource.save()

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
        resource_instances = resource_serializer.save()

        relationship_serializer = IIIFResourceRelationshipCreateSerializer(
            data=validated_data.get("relationships"), many=True
        )
        relationship_serializer.is_valid(raise_exception=True)
        relationship_instances = relationship_serializer.save()
        self.update_parent_resources_with_child_resource_ids(relationship_instances)
        self._data = {
            "resources": resource_serializer.data,
            "relationships": relationship_serializer.data,
        }
        return resource_instances + relationship_instances


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

    indexable_iiif_fields = [
        {"key": "label", "indexable_type": "descriptive", "index_as": "text"},
        {
            "key": "requiredStatement",
            "indexable_type": "descriptive",
            "index_as": "text",
        },
        {"key": "summary", "indexable_type": "descriptive", "index_as": "text"},
        {"key": "metadata", "indexable_type": "metadata", "index_as": "text"},
        {"key": "navDate", "indexable_type": "descriptive", "index_as": "date"},
    ]

    def _text_indexable(
        self,
        type,
        subtype,
        value,
        language,
    ):
        return {
            "type": type,
            "subtype": subtype.lower(),
            "indexable_text": BeautifulSoup(value, "html.parser").text,
            "original_content": str({subtype: bleach.clean(value)}),
            "language": language,
        }

    def _date_indexable(
        self,
        type,
        subtype,
        value,
    ):
        try:
            parsed_date = dateutil.parser.parse(value)
        except ValueError:
            parsed_date = None
        if parsed_date:
            return {
                "type": type,
                "subtype": subtype.lower(),
                "indexable_date_range_start": parsed_date,
                "indexable_date_range_end": parsed_date,
                "original_content": str({subtype: bleach.clean(value)}),
            }

    def _normalise_field(self, field_data):
        if isinstance(field_data, dict):
            return [field_data]
        elif isinstance(field_data, list):
            return field_data
        else:
            return [{"none": field_data}]

    def _normalise_language(self, language):
        if language in ["@none", "none"]:
            return default_lang
        else:
            return language

    def _indexables_from_field(
        self,
        field_instance,
        key=None,
        indexable_type="descriptive",
        index_as="text",
    ):
        indexables = []
        if not field_instance.get("label"):
            for val_lang, vals in field_instance.items():
                lang = self._normalise_language(val_lang)
                if vals:
                    for str_value in map(str, vals):
                        if index_as == "text":
                            indexables.append(
                                self._text_indexable(
                                    type=indexable_type,
                                    subtype=key,
                                    value=str_value,
                                    language=lang,
                                )
                            )
                        elif index_as == "date":
                            indexables.append(
                                self._date_indexable(
                                    type=indexable_type,
                                    subtype=key,
                                    value=str_value,
                                )
                            )
        else:
            subtype = key
            label_values = field_instance.get("label", {})
            if field_values := field_instance.get("value"):
                for val_lang, vals in field_values.items():
                    if labels := label_values.get(val_lang):
                        subtype = labels[0]
                    lang = self._normalise_language(val_lang)
                    for str_value in map(str, vals):
                        if index_as == "text":
                            indexables.append(
                                self._text_indexable(
                                    type=indexable_type,
                                    subtype=subtype,
                                    value=str_value,
                                    language=lang,
                                )
                            )
                        elif index_as == "date":
                            indexables.append(
                                self._date_indexable(
                                    type=indexable_type,
                                    subtype=subtype,
                                    value=str_value,
                                )
                            )
        logger.info(indexables)
        return indexables

    def to_indexables(self, instance):
        indexables = []
        for field_lookup in self.indexable_iiif_fields:
            if field := instance.iiif_json.get(field_lookup.get("key")):
                norm_field = self._normalise_field(field)
                for field_instance in norm_field:
                    indexables.extend(
                        self._indexables_from_field(field_instance, **field_lookup)
                    )
        return indexables
