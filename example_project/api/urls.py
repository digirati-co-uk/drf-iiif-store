from django.urls import path, include
from rest_framework import routers

app_name = 'api'
router = routers.DefaultRouter(trailing_slash=False)
include_urls = [
    path("iiif_store/", include(("iiif_store.urls.api"))),
]
urlpatterns = router.urls + include_urls
