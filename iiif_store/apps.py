from django.apps import AppConfig


class IIIFStoreConfig(AppConfig):
    name = "iiif_store"

    def ready(self):
        from .signals import (
            index_iiif_resource,
        )
