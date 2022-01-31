# drf-iiif-store
IIIF Store Django library using Django REST Framework


# Testing

```
cd tests
poetry run pytest
```


# Endpoints

| Endpoint | View | URL Pattern Name |
| -- | -- | -- |
|`/api/iiif_store/` | `rest_framework.routers.view` | `api:iiif_store:api-root`|
|`/api/iiif_store/\.<format>/` | `rest_framework.routers.view` | `api:iiif_store:api-root`|
|`/api/iiif_store/iiif/` | `iiif_store.views.IIIFResourceViewSet` | `api:iiif_store:iiifresource-list`|
|`/api/iiif_store/iiif/<id>/` | `iiif_store.views.IIIFResourceViewSet` | `api:iiif_store:iiifresource-detail`|
|`/api/iiif_store/iiif/<id>\.<format>/` | `iiif_store.views.IIIFResourceViewSet` | `api:iiif_store:iiifresource-detail`|
|`/api/iiif_store/iiif\.<format>/` | `iiif_store.views.IIIFResourceViewSet` | `api:iiif_store:iiifresource-list`|
| -- | -- | -- |
|`/iiif/` | `iiif_store.views.IIIFResourcePublicViewSet` | `iiif_store:iiifresource-list`|
|`/iiif/<id>/` | `iiif_store.views.IIIFResourcePublicViewSet` | `iiif_store:iiifresource-detail`|
|`/iiif/<iiif_type>/` | `iiif_store.views.IIIFResourcePublicViewSet` | `iiif_store:iiifresource-list_iiif_type`|
|`/iiif/<iiif_type>/<id>/` | `iiif_store.views.IIIFResourcePublicViewSet` | `iiif_store:iiifresource-iiif_detail`|

