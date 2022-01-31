from rest_framework import routers
from ..views import (
    IIIFResourcePublicViewSet,
)

app_name = "iiif_store"

router = routers.SimpleRouter()
router.register("iiif", IIIFResourcePublicViewSet)
urlpatterns = router.urls
