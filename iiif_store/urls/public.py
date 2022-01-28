from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from ..views import (
    StoredIIIF
)

app_name = 'iiif_store'

urlpatterns = [
    path(
        "<str:iiif_type>/<uuid:id>",
        StoredIIIF.as_view(),
        name="iiif_store.public.stored_iiif",
    ),
]
urlpatterns = format_suffix_patterns(urlpatterns)
