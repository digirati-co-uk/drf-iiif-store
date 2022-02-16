from rest_framework import routers
from ..views import (
    IIIFResourceViewSet,
    IIIFResourceSearchViewSet,
)

app_name = "iiif_store"

router = routers.DefaultRouter(trailing_slash=False)
router.register("iiif", IIIFResourceViewSet)
router.register("search", IIIFResourceSearchViewSet)
urlpatterns = router.urls
