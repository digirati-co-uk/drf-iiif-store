from rest_framework import routers
from ..views import (
    IIIFResourceAPIViewSet,
    IIIFServicesAPIViewSet,
    IIIFResourceAPISearchViewSet,
)

app_name = "iiif_store"


class IIIFStoreAPIRootView(routers.APIRootView):
    """
    REST APIs for the IIIF Store API app.
    """

    pass


class IIIFStoreAPIRouter(routers.DefaultRouter):
    APIRootView = IIIFStoreAPIRootView


router = IIIFStoreAPIRouter()
router.register("iiif", IIIFResourceAPIViewSet)
router.register("services", IIIFServicesAPIViewSet, basename="services")
router.register("search", IIIFResourceAPISearchViewSet, basename="search")
urlpatterns = router.urls
