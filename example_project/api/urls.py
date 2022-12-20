from django.urls import path, include
from rest_framework import routers


class ExampleProjectAPIRootView(routers.APIRootView):
    """
    REST APIs for the Example Project API app.
    """

    pass


class ExampleProjectAPIRouter(routers.DefaultRouter):
    APIRootView = ExampleProjectAPIRootView

    def get_api_root_view(self, api_urls=None):
        return self.APIRootView.as_view(
            api_root_dict={
                "search_service": "search_service:api-root",
                "iiif_store": "iiif_store:api-root",
            }
        )


router = ExampleProjectAPIRouter()

app_name = "api"
include_urls = [
    path("iiif_store/", include(("iiif_store.urls.api"))),
    path("search_service/", include(("search_service.urls.api"))),
]
urlpatterns = router.urls + include_urls
