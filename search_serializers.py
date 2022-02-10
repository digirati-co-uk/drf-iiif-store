import logging
import pytz
import json
import itertools

from copy import deepcopy
from datetime import datetime

from django.utils.translation import get_language
from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchHeadline
from django.db.models.functions import Concat
from django.db.models import F, Value, CharField
from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers
from .indexable_utils import clean_values
from .models import Indexables, IIIFResource, Context
from .serializer_utils import calc_offsets, flatten_iiif_descriptive
from .langbase import LANGBASE


default_lang = get_language()

logger = logging.getLogger(__name__)

utc = pytz.UTC


class ContextSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for Context objects, i.e. for the site, project, collection, etc
    that might be associated with a IIIF resource.
    """

    class Meta:
        model = Context
        fields = ["url", "id", "type", "slug"]
        extra_kwargs = {
            "url": {
                "view_name": "api:search_service:context-detail",
                "lookup_field": "slug",
            }
        }


class MadocIDSiteURNField(serializers.Serializer):
    """ """

    def to_representation(self, value):
        return value.split("|")[-1]


class IIIFCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for IIIF Prezi 3 resources.
    """

    class Meta:
        model = IIIFResource
        fields = [
            "madoc_id",
            "madoc_thumbnail",
            "id",
            "type",
            "label",
            "thumbnail",
            "summary",
            "metadata",
            "rights",
            "provider",
            "requiredStatement",
            "navDate",
            "first_canvas_id",
            "first_canvas_json",
            "contexts",
        ]


class IIIFSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for IIIF Prezi 3 resources.
    """

    contexts = ContextSerializer(read_only=True, many=True)
    madoc_id = MadocIDSiteURNField(read_only=True)

    class Meta:
        model = IIIFResource
        fields = [
            "url",
            "madoc_id",
            "madoc_thumbnail",
            "id",
            "type",
            "label",
            "thumbnail",
            "summary",
            "metadata",
            "rights",
            "provider",
            "requiredStatement",
            "navDate",
            "first_canvas_id",
            "first_canvas_json",
            "contexts",
        ]
        extra_kwargs = {"url": {"view_name": "api:search_service:iiif-detail", "lookup_field": "id"}}


class IIIFSummary(serializers.HyperlinkedModelSerializer):
    """
    Serializer that produces a summary of a IIIF resource for return in lists
    of search results or other similar nested views
    """

    contexts = ContextSerializer(read_only=True, many=True)
    madoc_id = MadocIDSiteURNField(read_only=True)

    class Meta:
        model = IIIFResource
        fields = [
            "url",
            "madoc_id",
            "madoc_thumbnail",
            "id",
            "type",
            "label",
            "first_canvas_id",
            "contexts",
        ]
        extra_kwargs = {"url": {"view_name": "api:search_service:iiif-detail", "lookup_field": "id"}}


class ContextSummarySerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer that produces a summary of a Context object for return in lists of
    search results or other similar nested views
    """

    id = serializers.SerializerMethodField(source="*")

    def get_id(self, obj):
        if obj.type == "Manifest" and "|" in obj.id:
            return obj.id.split("|")[-1]
        else:
            return obj.id

    class Meta:
        model = Context
        fields = ["url", "id", "type"]
        extra_kwargs = {
            "url": {
                "view_name": "api:search_service:context-detail",
                "lookup_field": "slug",
            }
        }


class IndexablesSummarySerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer that produces a summary of an individually indexed "field" or text
    resource for return in lists of results or other similar nested views
    """

    rank = serializers.FloatField(default=None, read_only=True)
    snippet = serializers.CharField(default=None, read_only=True)
    language = serializers.CharField(
        default=None, read_only=None, source="language_iso639_1"
    )
    bounding_boxes = serializers.SerializerMethodField()

    @staticmethod
    def get_bounding_boxes(obj):
        return calc_offsets(obj)

    class Meta:
        model = Indexables
        fields = [
            "type",
            "subtype",
            "group_id",
            "snippet",
            "language",
            "rank",
            "bounding_boxes",
        ]


class IIIFSearchSummarySerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer that produces the summarized search results.
    """

    contexts = ContextSummarySerializer(read_only=True, many=True)
    hits = serializers.SerializerMethodField("get_hits")
    has_matching_parts = serializers.SerializerMethodField("get_has_matching_parts")
    # resource_id = serializers.CharField(source="madoc_id", read_only=True)
    resource_id = MadocIDSiteURNField(source="madoc_id", read_only=True)
    resource_type = serializers.CharField(source="type")
    rank = serializers.SerializerMethodField("get_rank")
    sortk = serializers.SerializerMethodField("get_sortk")
    metadata = serializers.SerializerMethodField("get_metadata")
    rights = serializers.URLField()
    provider = serializers.JSONField()
    requiredStatement = serializers.JSONField()

    def get_sortk(self, iiif):
        """
        Generate a sort key to associate with the object.
        """
        order_key = None
        if self.context.get("request"):
            order_key = self.context["request"].data.get("sort_order", None)
        if not order_key:
            return self.get_rank(iiif=iiif)
        logger.debug(f"Order key {order_key}")
        if (
            isinstance(order_key, dict)
            and order_key.get("type")
            and order_key.get("subtype")
        ):
            val = order_key.get("value_for_sort", "indexable")
            sort_qs = (
                Indexables.objects.filter(
                    iiif=iiif,
                    type__iexact=order_key.get("type"),
                    subtype__iexact=order_key.get("subtype"),
                )
                .values(val)
                .first()
            )
            if sort_qs:
                sort_keys = list(sort_qs.values())[0]
                return sort_keys
        else:
            logger.debug("We have no type or subtype on order key")
        return self.get_sort_default(order_key=order_key)

    @staticmethod
    def get_sort_default(order_key):
        if value_for_sort := order_key.get("value_for_sort"):
            if value_for_sort.startswith("indexable_int"):
                return 0
            elif value_for_sort.startswith("indexable_float"):
                return 0.0
            elif value_for_sort.startswith("indexable_date"):
                return datetime.min.replace(tzinfo=utc)
            else:
                return ""

        if order_key.get("type") and order_key.get("subtype"):
            return ""

        return 0.0

    def get_rank(self, iiif):
        """
        Serializer method that calculates the average rank from the hits associated
        with this search result
        """
        try:
            return max([h["rank"] for h in self.get_hits(iiif=iiif)])
        except TypeError or ValueError:
            return 1.0

    def get_has_matching_parts(self, iiif):
        if self.context.get("request"):
            if self.context["request"].data.get("contains_hit_kwargs"):
                qs = (
                    Indexables.objects.filter(
                        **self.context["request"].data["contains_hit_kwargs"],
                        iiif__contexts__associated_iiif__madoc_id=iiif.madoc_id,
                    )
                    .distinct()
                    .values(
                        part_id=F("iiif__id"),
                        part_label=F("iiif__label"),
                        part_madoc_id=F("iiif__madoc_id"),
                        part_type=F("iiif__type"),
                        part_first_canvas_id=F("iiif__first_canvas_id"),
                        part_thumbnail=F("iiif__madoc_thumbnail"),
                    )
                )
                logger.debug(
                    f"Contains queryset {self.context['request'].data['contains_hit_kwargs']}"
                )
                if qs:
                    return qs

    def get_hits(self, iiif):
        """
        Serializer method that calculates the hits to return along with this search
        result
        """
        # Rank must be greater than 0 (i.e. this is some kind of hit)
        filter_kwargs = {"rank__gt": 0.0}
        # Filter the indexables to query against to just those associated with this IIIF resource
        qs = Indexables.objects.filter(iiif=iiif)
        search_query = None
        if self.context.get("request"):
            if self.context["request"].data.get("hits_filter_kwargs"):
                # We have a dictionary of queries to use, so we use that
                search_query = (
                    self.context["request"]
                    .data["hits_filter_kwargs"]
                    .get("search_vector", None)
                )
            else:
                # Otherwise, this is probably a simple GET request, so we construct the queries from params
                search_string = self.context["request"].query_params.get(
                    "fulltext", None
                )
                language = self.context["request"].query_params.get(
                    "search_language", None
                )
                search_type = self.context["request"].query_params.get(
                    "search_type", "websearch"
                )
                if search_string:
                    if language:
                        search_query = SearchQuery(
                            search_string, config=language, search_type=search_type
                        )
                    else:
                        search_query = SearchQuery(
                            search_string, search_type=search_type
                        )
                else:
                    search_query = None
        if search_query:
            # Annotate the results in the queryset with rank, and with a snippet
            qs = (
                qs.annotate(
                    rank=SearchRank(
                        F("search_vector"), search_query, cover_density=True
                    ),
                    snippet=Concat(
                        Value("'"),
                        SearchHeadline(
                            "original_content",
                            search_query,
                            max_words=50,
                            min_words=25,
                            max_fragments=3,
                        ),
                        output_field=CharField(),
                    ),
                    fullsnip=SearchHeadline(
                        "indexable",
                        search_query,
                        start_sel="<start_sel>",
                        stop_sel="<end_sel>",
                        highlight_all=True,
                    ),
                )
                .filter(search_vector=search_query, **filter_kwargs)
                .order_by("-rank")
            )
        else:
            return
        # Use the Indexables summary serializer to return the hit list
        serializer = IndexablesSummarySerializer(instance=qs, many=True)
        return serializer.data

    def get_metadata(self, iiif):
        """If the context has had the `metadata_fields` property set
        by the calling view's `get_serializer_context`, then return only
        the metdata items defined by this configuration. The metadata_fields
        config object should be as follows:
        metadata_fields = {lang_code: [label1, label2]}
        e.g.
        metadata_fields = {'en': ['Author', 'Collection']}

        If metadata_fields has not been set, then all the metadata associated
        with the iiif object is returned.
        """
        if self.context.get("request"):
            if metadata_fields := self.context["request"].data.get("metadata_fields"):
                logger.debug("We have metadata fields on the incoming request")
                logger.debug(f"{metadata_fields}")
                filtered_metadata = []
                if iiif.metadata:
                    for metadata_item in iiif.metadata:
                        for lang, labels in metadata_fields.items():
                            for label in labels:
                                if label in metadata_item.get("label", {}).get(
                                    lang, []
                                ):
                                    filtered_metadata.append(metadata_item)
                return filtered_metadata
        return iiif.metadata

    class Meta:
        model = IIIFResource
        fields = [
            "url",
            "resource_id",
            "resource_type",
            "madoc_thumbnail",
            "thumbnail",
            "id",
            "rank",
            "label",
            "contexts",
            "hits",
            "sortk",
            "metadata",
            "first_canvas_id",
            "has_matching_parts",
            "rights",
            "provider",
            "requiredStatement",
        ]
        extra_kwargs = {"url": {"view_name": "api:search_service:iiif-detail", "lookup_field": "id"}}


class AutocompleteSerializer(serializers.ModelSerializer):
    """
    Serializer for the Indexables for autocompletion
    """

    class Meta:
        model = Indexables
        fields = [
            "indexable",
        ]


class BaseModelToIndexablesSerializer(serializers.Serializer):
    @property
    def data(self):
        """Bypasses the wrapping of the returned value with a ReturnDict from the serializers.Serializer data method.
        This allows the serializer to return a list of items from an individual instance.
        """
        if not hasattr(self, "_data"):
            self._data = self.to_representation(self.instance)
        return self._data

    def to_indexables(self, instance):
        return [{}]

    def to_representation(self, instance):
        resource_fields = {
            "resource_id": instance.id,
            "resource_content_type": ContentType.objects.get_for_model(instance).pk,
        }
        indexables_data = []
        for indexable in self.to_indexables(instance):
            indexables_data.append({**resource_fields, **indexable})
        return indexables_data


class IndexablesCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Indexables
        fields = "__all__"


class IndexablesSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for the Indexables, i.e. the indexed objects that are used to
    drive search and which are associated with a IIIF resource
    """

    iiif = IIIFSummary(read_only=True)

    class Meta:
        model = Indexables
        fields = [
            "url",
            "resource_id",
            "content_id",
            "original_content",
            "group_id",
            "indexable",
            "indexable_date_range_start",
            "indexable_date_range_end",
            "indexable_int",
            "indexable_float",
            "indexable_json",
            "selector",
            "type",
            "subtype",
            "language_iso639_2",
            "language_iso639_1",
            "language_display",
            "language_pg",
            "iiif",
            "search_vector",
        ]
        extra_kwargs = {"url": {"view_name": "api:search_service:indexables-detail", "lookup_field": "id"}}

    def create(self, validated_data):
        # On create, associate the resource with the relevant IIIF resource
        # via the Madoc identifier for that object
        resource_id = validated_data.get("resource_id")
        content_id = validated_data.get("content_id")
        iiif = IIIFResource.objects.get(madoc_id=resource_id)
        validated_data["iiif"] = iiif
        if content_id and resource_id:
            print(
                f"Deleting any indexables for {resource_id} with content id {content_id}"
            )
            Indexables.objects.filter(
                resource_id=resource_id, content_id=content_id
            ).delete()
        return super(IndexablesSerializer, self).create(validated_data)


class CaptureModelSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for the Indexables, i.e. the indexed objects that are used to
    drive search and which are associated with a IIIF resource
    """

    iiif = IIIFSummary(read_only=True)

    class Meta:
        model = Indexables
        fields = [
            "url",
            "resource_id",
            "content_id",
            "original_content",
            "group_id",
            "indexable",
            "indexable_date_range_start",
            "indexable_date_range_end",
            "indexable_int",
            "indexable_float",
            "indexable_json",
            "selector",
            "type",
            "subtype",
            "language_iso639_2",
            "language_iso639_1",
            "language_display",
            "language_pg",
            "iiif",
        ]
        extra_kwargs = {"url": {"view_name": "api:search_service:indexables-detail", "lookup_field": "id"}}

    def create(self, validated_data):
        # On create, associate the resource with the relevant IIIF resource
        # via the Madoc identifier for that object
        resource_id = validated_data.get("resource_id")
        content_id = validated_data.get("content_id")
        iiif = IIIFResource.objects.get(madoc_id=resource_id)
        validated_data["iiif"] = iiif
        if content_id and resource_id:
            print(
                f"Deleting any indexables for {resource_id} with content id {content_id}"
            )
            Indexables.objects.filter(
                resource_id=resource_id, content_id=content_id
            ).delete()
        return super(CaptureModelSerializer, self).create(validated_data)


def contexts_create_update(instance, local_contexts):
    """
    Function to get or create any context resources that are associated with a IIIF Resource instance
    and add those contexts to that resource

    :param instance: instance of the IIIF Resource model
    :param local_contexts: list of context object dicts
    :return:
    """
    if local_contexts:
        c_objs = [
            Context.objects.get_or_create(**context) for context in local_contexts
        ]
        c_objs_set = [c_obj for c_obj, _ in c_objs]
        instance.contexts.set(c_objs_set)
        instance.save()


def indexables_create_update(iiif3_resource, instance, delete_existing_indexables=True):
    """
    N.B. we should probably be deleting the existing indexables to avoid issues where orphaned indexables
    are left hanging around. Parameter defaults to True.

    Function to create the indexables for a IIIF resource

    :param iiif3_resource: IIIF Presentation API 3 resource
    :param instance: IIIF Resource model instance
    :param delete_existing_indexables: clean up the old indexables.
    :return:
    """
    if iiif3_resource:
        # Flatten the IIIF metadata and descriptive properties into a list of indexables
        indexable_list = flatten_iiif_descriptive(
            iiif=iiif3_resource, default_language=default_lang, lang_base=LANGBASE
        )
        if delete_existing_indexables:
            instance.indexables.all().delete()
        if indexable_list:
            # Create the indexables
            for _indexable in indexable_list:
                indexable_obj = Indexables(
                    **_indexable, iiif=instance, resource_id=instance.madoc_id
                )
                indexable_obj.save()


def children_create_update(instance, iiif3_resource, validated_data, local_contexts):
    """
    Function to create or update any child IIIF Resources that are derived from the IIIF Resource

    :param instance: IIIF Resource instance
    :param iiif3_resource: iiif3 presentation API resource (as a dict/object)
    :param validated_data: validated data from the request/serializer
    :param local_contexts: list of context objects from the parent
    :return:
    """
    subitems = []
    if iiif3_resource.get("items"):
        subitems += iiif3_resource["items"]
    if iiif3_resource.get("structures"):
        subitems += iiif3_resource["structures"]
    if subitems:
        # Chain any lists, because ranges sometimes contain lists of ranges, rather than just ranges
        # or contain lists of lists of lists, etc.
        if any([isinstance(s, list) for s in subitems]):
            iterable_subitems = itertools.chain.from_iterable(subitems)
        else:
            iterable_subitems = subitems
        for num, item in enumerate(iterable_subitems):
            # Only ingest a canvas if it's part of a manifest, otherwise, this is
            # a duplicate as canvases in Ranges are just pointers to the items on the
            # manifest
            if (
                item.get("type") == "Canvas"
                and instance.type == "Manifest"
                and validated_data.get("cascade_canvases")
            ) or (item.get("type") == "Range" and validated_data.get("cascade")):
                child_dict = dict(
                    iiif3_resource=item,
                    resource_contexts=local_contexts,
                    madoc_id=":".join(
                        [instance.madoc_id, item["type"].lower(), str(num)]
                    ),
                    madoc_thumbnail=None,
                    child=True,
                    parent=instance.madoc_id,
                    manifest=validated_data.get("manifest"),
                    cascade=validated_data.get("cascade"),
                    cascade_canvases=validated_data.get("cascade_canvases"),
                    id=item.get("id"),
                )
                # Catch cases where the Range or Canvas already exists, e.g. if a Manifest has been
                # added and then deleted at some point. Currently, deleting a IIIF resource does not
                # delete any other resources that have this resource as their parent context.
                existing_nested = IIIFResource.objects.filter(
                    madoc_id=child_dict["madoc_id"]
                ).first()
                if existing_nested:
                    logger.debug(
                        f"Nested item {child_dict.get('madoc_id')} already exists"
                    )
                if not existing_nested:
                    nested = IIIFCreateUpdateSerializer(data=child_dict)
                else:
                    nested = IIIFCreateUpdateSerializer(
                        existing_nested, data=child_dict, partial=True
                    )
                if nested.is_valid(raise_exception=False):
                    logger.debug(
                        f"Successful nested item ID was: {child_dict.get('madoc_id')}"
                    )
                    nested.save()
                else:
                    logger.error(
                        f"Failed nested item ID was: {child_dict.get('madoc_id')}"
                    )
                    logger.error(nested.errors)


def build_iiif_resource_data(validated_data, contexts=None):
    """
    Function to parse the incoming data and return:

    * a IIIF 3 presentation API resource
    * a dictionary that is used to pass to the IIIF Resource serializer
    * the local contexts for this object

    :param validated_data:
    :param contexts:
    :return:
    """

    local_dict = {
        "madoc_id": validated_data.get("madoc_id"),
        "madoc_thumbnail": validated_data.get("madoc_thumbnail"),
    }
    logger.info("Local dict inside")
    logger.info(local_dict)

    # Parse the incoming IIIF Presentation API 3 manifest to extract key fields
    # for indexing.
    if (iiif3_resource := validated_data.get("iiif3_resource")) is not None:
        for k in [
            "id",
            "type",
            "label",
            "summary",
            "metadata",
            "rights",
            "provider",
            "navDate",
        ]:
            local_dict[k] = iiif3_resource.get(k)
        for cleanable_key in [
            "requiredStatement",
        ]:
            cleanable = iiif3_resource.get(cleanable_key)
            if cleanable:
                local_dict[cleanable_key] = clean_values(cleanable)
    # Get the first canvas JSON (for use in list results, thumbnail extraction, etc)
    first_canvas_json = get_first_canvas(iiif3_resource, validated_data.get("manifest"))
    if first_canvas_json:
        local_dict["first_canvas_json"] = first_canvas_json
        local_dict["first_canvas_id"] = first_canvas_json.get("id")
    # Get the thumbnail
    thumbnail_json = get_iiif_resource_thumbnail_json(
        iiif3_resource,
        first_canvas_json=first_canvas_json,
        fallback=settings.THUMBNAIL_FALLBACK,
    )
    if thumbnail_json:
        if isinstance(thumbnail_json, list):
            local_dict["madoc_thumbnail"] = format_thumbnail_url(thumbnail_json)
            logger.info(local_dict["madoc_thumbnail"])
        local_dict["thumbnail"] = thumbnail_json
    if contexts is not None:
        local_contexts = deepcopy(contexts)
    else:
        local_contexts = []
    return local_dict, iiif3_resource, local_contexts


class IIIFCreateUpdateSerializer(serializers.Serializer):
    cascade = serializers.BooleanField(default=False)
    cascade_canvases = serializers.BooleanField(default=False)
    resource_contexts = serializers.ListField(allow_empty=True, allow_null=True)
    iiif3_resource = serializers.JSONField()
    manifest = serializers.JSONField(allow_null=True)
    madoc_id = serializers.CharField()
    id = serializers.CharField()
    madoc_thumbnail = serializers.URLField(allow_null=True, allow_blank=True)
    child = serializers.BooleanField(default=False)
    parent = serializers.CharField(allow_null=True, allow_blank=True)

    def to_representation(self, instance):
        """
        We are accepting data in in the form of the parsed data being provided from the request by
        the IIIFCreateUpdateParser. However, we want to return a standard IIIFResource object, so
        override the to_representation method.
        :param instance:
        :return:
        """
        return IIIFSerializer(
            instance, context={"request": self.context["request"]}
        ).data

    def create(self, validated_data):
        logger.info("Create method invoked")
        instance = None
        # if madoc_site_urn := request_madoc_site_urn(self.context["request"]):
        #     logger.debug(f"Got madoc site urn: {madoc_site_urn}")
        #     validated_data["madoc_id"] = f"{madoc_site_urn}|{validated_data['madoc_id']}"
        local_dict, iiif3_resource, local_contexts = build_iiif_resource_data(
            validated_data=validated_data,
            contexts=validated_data.get("resource_contexts"),
        )
        """
        If this is a Range or Canvas, ensure we have the right _parent_ IIIFResource to create the
        foreign key relationship. 
        
        N.B. this doesn't happen on an .update() as the resource parent does not change
        """
        parent_object = None
        if (validated_data.get("child") is True) and (
            validated_data.get("parent") is not None
        ):
            parent_object = IIIFResource.objects.get(
                madoc_id=validated_data.get("parent")
            )
        # Validate the serialized data and save the object
        serializer = IIIFCreateSerializer(data=local_dict)
        if serializer.is_valid(raise_exception=True):  # Check it's valid
            logger.debug("Saving object")
            instance = serializer.save()
        else:
            logger.error(serializer.errors)
        """
        Add all of the contexts to the object, including the object itself.
        Again, this is only done on .create() as on an .update() the object
        already has itself and its parent in the context
        """
        if iiif3_resource:  # Add myself to the context(s)
            if local_dict.get("type"):
                local_contexts += [
                    {"id": validated_data.get("madoc_id"), "type": local_dict["type"]}
                ]
                local_contexts += [{"id": local_dict["id"], "type": local_dict["type"]}]
        if parent_object is not None:
            # If I'm, e.g. a Canvas or Range, add my parent manifest to the list of context(s)
            local_contexts += [{"id": parent_object.id, "type": parent_object.type}]
            local_contexts += [
                {"id": parent_object.madoc_id, "type": parent_object.type}
            ]
        # Create contexts
        if local_contexts:
            contexts_create_update(instance=instance, local_contexts=local_contexts)
        # Create the indexed data for search
        if iiif3_resource:
            indexables_create_update(instance=instance, iiif3_resource=iiif3_resource)
        # Create or update any child IIIF resources
        if local_contexts and iiif3_resource:
            children_create_update(
                instance=instance,
                iiif3_resource=iiif3_resource,
                validated_data=validated_data,
                local_contexts=local_contexts,
            )
        return instance

    def update(self, instance, validated_data):
        existing_contexts = [
            {"id": c.id, "type": c.type} for c in instance.contexts.all()
        ]
        # Add any contexts on the incoming request to the list if there are any
        if (updated_contexts := validated_data.get("contexts")) is not None:
            existing_contexts += updated_contexts
        local_dict, iiif3_resource, local_contexts = build_iiif_resource_data(
            validated_data=validated_data,
            contexts=existing_contexts,
        )
        # Update the IIIF Resource object
        serializer = IIIFCreateSerializer(instance, data=local_dict, partial=True)
        if serializer.is_valid(raise_exception=True):
            instance = serializer.save()
        # Create/update the indexables
        if iiif3_resource:
            indexables_create_update(instance=instance, iiif3_resource=iiif3_resource)
        # Create/update the contexts
        if local_contexts:
            contexts_create_update(instance=instance, local_contexts=local_contexts)
        # Create/update any child IIIF resources, e.g. Ranges or Canvases for a Manifest
        if local_contexts and iiif3_resource:
            children_create_update(
                instance=instance,
                iiif3_resource=iiif3_resource,
                validated_data=validated_data,
                local_contexts=local_contexts,
            )
        # If 'prefetch_related' has been applied to a queryset, we need to
        # forcibly invalidate the prefetch cache on the instance.
        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}
        return instance
