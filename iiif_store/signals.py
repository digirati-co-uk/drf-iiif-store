import logging

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django_q.tasks import async_task

from .models import IIIFResource
from .tasks import IIIFResourceIndexingTask
from .settings import iiif_store_settings
from .utils import run_task


logger = logging.getLogger(__name__)


@receiver(post_save, sender=IIIFResource)
def index_iiif_resource(sender, instance, **kwargs):
    if iiif_store_settings.INDEX_IIIF_RESOURCES:
        task = IIIFResourceIndexingTask
        if iiif_store_settings.ASYNC_INDEXING:
            logger.debug(f"Queuing the IIIFResourceIndexingTask for: ({instance.id})")
            async_task(run_task, task, object_id=instance.id)
        else: 
            logger.debug(f"Running the IIIFResourceIndexingTask for: ({instance.id})")
            sync_task = task(object_id=instance.id)
            sync_task.run()


@receiver(pre_delete, sender=IIIFResource)
def delete_iiif_manifest_partof_relations(sender, instance, **kwargs):
    if instance.iiif_type in ["manifest"]:
        resources = IIIFResource.objects.filter(
            id__in=instance.relationship_targets.filter(type="isPartOf").values_list(
                "source_id", flat=True
            )
        )
        logger.debug(
            f"Deleting IIIFResources with isPartOf relationship: ({instance.id}, {resources.count()})"
        )
        resources.delete()
