import logging

# Django Imports
from rest_framework import generics
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

# Local imports
from .models import (
        StoredIIIFResource, 
        )

from .serializers import (
    IIIFSerializer,
    StoredIIIFResourceSerializer,
)

logger = logging.getLogger(__name__)


@api_view(["GET"])
def api_root(request, format=None):
    return Response(
        {
            'iiif_store': 'Available'
        }
    )


class StoredIIIF(generics.RetrieveAPIView):
    queryset = StoredIIIFResource.objects.all()
    serializer_class = IIIFSerializer
    lookup_field = "id"


class StoredIIIFResourceViewSet(viewsets.ModelViewSet): 
    queryset = StoredIIIFResource.objects.all()
    serializer_class = StoredIIIFResourceSerializer
    lookup_field = "id" 
