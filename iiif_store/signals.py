import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import IIIFResource
from .tasks import IIIFResourceIndexingTask
from .settings import iiif_store_settings

logger = logging.getLogger(__name__)


@receiver(post_save, sender=IIIFResource)
def index_iiif_resource(sender, instance, **kwargs):
    if iiif_store_settings.INDEX_IIIF_RESOURCES:
        logger.debug(f"Running the IIIFResourceIndexingTask for: ({instance.id})")
        task = IIIFResourceIndexingTask(instance.id)
        task.run()
