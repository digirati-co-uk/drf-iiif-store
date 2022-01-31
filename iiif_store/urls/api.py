from rest_framework import routers
from ..views import (
    IIIFResourceViewSet,
)

app_name = "iiif_store"

router = routers.DefaultRouter(trailing_slash=False)
router.register("iiif", IIIFResourceViewSet)
urlpatterns = router.urls
