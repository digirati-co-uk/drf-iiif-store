import logging

# Django Imports
from rest_framework import viewsets
from rest_framework.decorators import action

# Local imports
from .models import (
    IIIFResource,
)
from .serializers import (
    IIIFSerializer,
    IIIFSummarySerializer,
    IIIFResourceSerializer,
    IIIFResourceSummarySerializer,
)

# This should be replaced by an import from a utils package.
from .utils import (
    ActionBasedSerializerMixin,
)

logger = logging.getLogger(__name__)


class IIIFResourceViewSet(ActionBasedSerializerMixin, viewsets.ModelViewSet):
    queryset = IIIFResource.objects.all()
    serializer_mapping = {
        "default": IIIFResourceSerializer,
        "list": IIIFResourceSummarySerializer,
    }
    lookup_field = "id"


class IIIFResourcePublicViewSet(
    ActionBasedSerializerMixin, viewsets.ReadOnlyModelViewSet
):
    queryset = IIIFResource.objects.all()
    serializer_mapping = {
            "default": IIIFSerializer,
            "list": IIIFSummarySerializer
            }
    lookup_field = "id"

    def get_queryset(self): 
        queryset = super().get_queryset()
        filter_kwargs = {}
        if iiif_type:= self.kwargs.get("iiif_type"): 
            filter_kwargs['iiif_type'] = iiif_type
        return queryset.filter(**filter_kwargs)

    @action(detail=False, url_path=r"(?P<iiif_type>[^/.]+)", url_name="list_iiif_type")
    def list_iiif_type(self, request, *args, **kwargs):
        """ List IIIF resources by type provided as the `iiif_type`
            kwarg passed in from the url_path. 
            """
        return self.list(request, *args, **kwargs)

    @action(detail=False, url_path=r"(?P<iiif_type>[^/.]+)/(?P<id>[^/]+)", url_name="iiif_detail")
    def retrieve_iiif(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

