from rest_framework import routers
from ..views import (
    IIIFResourceViewSet,
)

app_name = "iiif_store"

router = routers.DefaultRouter()
router.register("iiif", IIIFResourceViewSet)
urlpatterns = router.urls
