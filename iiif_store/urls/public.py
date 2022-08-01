from rest_framework import routers
from ..views import (
    IIIFResourcePublicViewSet,
    IIIFResourcePublicSearchViewSet,
)

app_name = "iiif_store"

router = routers.SimpleRouter()
router.register("iiif", IIIFResourcePublicViewSet)
router.register("search", IIIFResourcePublicSearchViewSet, basename="search")
urlpatterns = router.urls
