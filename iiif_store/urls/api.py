from rest_framework import routers
from ..views import (
    IIIFResourceViewSet,
    IIIFResourceSearchViewSet,
)

app_name = "iiif_store"

router = routers.DefaultRouter()
router.register("iiif", IIIFResourceViewSet)
router.register("search", IIIFResourceSearchViewSet, basename="search")
urlpatterns = router.urls
