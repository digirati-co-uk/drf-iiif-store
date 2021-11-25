import uuid
import urllib.parse
import logging

from django.contrib.gis.db import models
from model_utils.models import TimeStampedModel
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.conf import settings

logger = logging.getLogger(__name__)


class StoredIIIFResource(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) 
    original_id = models.URLField(verbose_name=_("IIIF id"), unique=True)
    iiif_type = models.CharField(max_length=30)
    label = models.JSONField(blank=True, null=True)
    thumbnail = models.JSONField(blank=True, null=True)
    iiif_json = models.JSONField(blank=True)

    def save(self, *args, **kwargs):
        iiif_store_public_url = settings.CANONICAL_HOSTNAME + reverse('iiif_store.public.stored_iiif', kwargs={
                'iiif_type': self.iiif_type, 
                'id': self.id
                })
        id_key = 'id'
        current_id = self.iiif_json.get(id_key)
        if not current_id: 
            logger.debug(f'Trying iiif2 @id for the id key')
            id_key = '@id'
            current_id = self.iiif_json.get(id_key)
        if current_id != iiif_store_public_url: 
            logger.debug(f'Updating iiif id for StoredIIIFResource to public url: ({current_id} -> {iiif_store_public_url})')
            iiif_json = self.iiif_json
            iiif_json[id_key] = iiif_store_public_url 
            self.iiif_json = iiif_json
        super().save(*args, **kwargs)
