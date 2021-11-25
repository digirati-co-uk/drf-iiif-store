from django.urls import path 
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework import routers
from ..views import (
        StoredIIIFResourceViewSet, 
        )


router = routers.DefaultRouter()
router.register('resource', StoredIIIFResourceViewSet)
urlpatterns = router.urls
