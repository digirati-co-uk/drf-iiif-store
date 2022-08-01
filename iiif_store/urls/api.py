from rest_framework import routers
from ..views import (
    IIIFResourceAPIViewSet,
    IIIFResourceAPISearchViewSet,
)

app_name = "iiif_store"

router = routers.DefaultRouter()
router.register("iiif", IIIFResourceAPIViewSet)
router.register("search", IIIFResourceAPISearchViewSet, basename="search")
urlpatterns = router.urls
