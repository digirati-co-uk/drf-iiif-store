import logging

from search_service.tasks import BaseSearchServiceIndexingTask

from .models import (
        IIIFResource, 
        )

from .serializers import (
        IIIFResourceToIndexableSerializer, 
        )

class IIIFResourceIndexingTask(BaseSearchServiceIndexingTask):
    model = IIIFResource
    serializer_class = IIIFResourceToIndexableSerializer
