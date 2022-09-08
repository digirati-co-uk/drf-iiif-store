from rest_framework import routers
from ..views import (
    IIIFResourceAPIViewSet,
    IIIFServicesAPIViewSet,
    IIIFResourceAPISearchViewSet,
)

app_name = "iiif_store"

router = routers.DefaultRouter()
router.register("iiif", IIIFResourceAPIViewSet)
router.register("services", IIIFServicesAPIViewSet, basename="services")
router.register("search", IIIFResourceAPISearchViewSet, basename="search")
urlpatterns = router.urls
