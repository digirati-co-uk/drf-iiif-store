import copy
import json
import pytest
import requests


app_endpoint = "api/iiif_store"
test_headers = {"Content-Type": "application/json", "Accept": "application/json"}

test_data_store = {}


@pytest.fixture
def simple_iiif3_manifest(tests_dir):
    return json.load(
        (tests_dir / "fixtures/simple_iiif3_manifest.json").open(encoding="utf-8")
    )


def test_iiif_store_api_root_get(http_service):
    status = 200
    response = requests.get(f"{http_service}/{app_endpoint}", headers=test_headers)
    assert response.status_code == status


def test_iiif_store_api_iiif_list_empty(http_service):
    test_endpoint = "iiif"
    status = 200
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    assert response.status_code == status
    response_json = response.json()
    assert response_json.get("count") == 0
    assert response_json.get("next") == None
    assert response_json.get("previous") == None
    assert response_json.get("results") == []


def test_iiif_store_api_iiif_create_manifest(http_service, simple_iiif3_manifest):
    post_json = {
        "iiif_json": simple_iiif3_manifest,
    }
    test_endpoint = "iiif"
    status = 201
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        headers=test_headers,
        json=post_json,
    )
    assert response.status_code == status
    response_json = response.json()
    assert response_json.get("resources") is not None
    assert response_json.get("relationships") is not None
    assert len(response_json.get("resources")) == 2
    assert len(response_json.get("relationships")) == 1

    for resource in response_json.get("resources"):
        test_data_store[resource.get("iiif_type")] = resource.get("id")

    manifest_response_json = response_json.get("resources")[0]
    assert manifest_response_json.get("id") is not None
    assert manifest_response_json.get("iiif_type") == 'manifest'
    assert manifest_response_json.get("original_id") == simple_iiif3_manifest.get("id")
    assert manifest_response_json.get("iiif_json").get(
        "id"
    ) != simple_iiif3_manifest.get("id")
    assert manifest_response_json.get("label") == simple_iiif3_manifest.get("label")
    assert (
        manifest_response_json.get("iiif_json").get("id")
        == f"http://localhost:8000/iiif/manifest/{test_data_store.get('manifest')}/"
    )
    expected_manifest = copy.deepcopy(simple_iiif3_manifest)
    expected_manifest.pop("id")
    manifest_response_json.get("iiif_json").pop("id")

    assert manifest_response_json.get("iiif_json") == expected_manifest


def test_iiif_store_api_iiif_list(http_service, simple_iiif3_manifest):
    test_endpoint = "iiif"
    status = 200
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    assert response.status_code == status
    response_json = response.json()
    assert response_json.get("count") == 2
    assert response_json.get("next") == None
    assert response_json.get("previous") == None
    assert len(response_json.get("results")) == 2

    manifest = response_json["results"][0]
    assert manifest.get("id") == test_data_store.get("manifest")
    assert manifest.get("iiif_type") == "manifest"
    assert manifest.get("original_id") == simple_iiif3_manifest.get("id")
    assert manifest.get("label") == simple_iiif3_manifest.get("label")
    assert manifest.get("thumbnail") == simple_iiif3_manifest.get("thumbnail")
    assert manifest.get("iiif_json") == None


def test_iiif_store_api_iiif_get_manifest(http_service, simple_iiif3_manifest):
    test_endpoint = f"iiif/{test_data_store.get('manifest')}"
    status = 200
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    assert response.status_code == status
    response_json = response.json()
    assert response_json.get("id") == test_data_store.get("manifest")
    assert response_json.get("iiif_type") == "manifest"
    assert response_json.get("original_id") == simple_iiif3_manifest.get("id")
    assert response_json.get("label") == simple_iiif3_manifest.get("label")
    assert response_json.get("thumbnail") == simple_iiif3_manifest.get("thumbnail")
    expected_manifest = copy.deepcopy(simple_iiif3_manifest)
    expected_manifest.pop("id")
    manifest_id = response_json.get("iiif_json").pop("id")
    assert (
        manifest_id
        == f"http://localhost:8000/iiif/manifest/{test_data_store.get('manifest')}/"
    )
    assert response_json.get("iiif_json") == expected_manifest


def test_iiif_store_api_iiif_get_canvas(http_service):
    test_endpoint = f"iiif/{test_data_store.get('canvas')}"
    status = 200
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    assert response.status_code == status
    response_json = response.json()
    assert response_json.get("id") == test_data_store.get("canvas")
    assert response_json.get("iiif_type") == "canvas"
    canvas_id = response_json.get("iiif_json").pop("id")
    assert (
        canvas_id
        == f"http://localhost:8000/iiif/canvas/{test_data_store.get('canvas')}/"
    )


@pytest.mark.skip(reason="Annotations not being created with default IIIF_RESOURCE_TYPES")
def test_iiif_store_api_iiif_get_annotation(http_service):
    test_endpoint = f"iiif/{test_data_store.get('annotation')}"
    status = 200
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    assert response.status_code == status
    response_json = response.json()
    assert response_json.get("id") == test_data_store.get("annotation")
    assert response_json.get("iiif_type") == "annotation"
    annotation_id = response_json.get("iiif_json").pop("id")
    assert (
        annotation_id
        == f"http://localhost:8000/iiif/annotation/{test_data_store.get('annotation')}/"
    )


@pytest.mark.skip(reason="AnnotationPages not being created with default IIIF_RESOURCE_TYPES")
def test_iiif_store_api_iiif_get_annotationpage(http_service):
    test_endpoint = f"iiif/{test_data_store.get('annotationpage')}"
    status = 200
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    assert response.status_code == status
    response_json = response.json()
    assert response_json.get("id") == test_data_store.get("annotationpage")
    assert response_json.get("iiif_type") == "annotationpage"
    annotationpage_id = response_json.get("iiif_json").pop("id")
    assert (
        annotationpage_id
        == f"http://localhost:8000/iiif/annotationpage/{test_data_store.get('annotationpage')}/"
    )


def test_iiif_store_public_iiif_list(http_service, simple_iiif3_manifest):
    test_endpoint = "iiif"
    status = 200
    response = requests.get(f"{http_service}/{test_endpoint}", headers=test_headers)
    assert response.status_code == status
    response_json = response.json()
    assert response_json.get("count") == 2
    assert response_json.get("next") == None
    assert response_json.get("previous") == None
    assert len(response_json.get("results")) == 2

    manifest = response_json["results"][0]
    assert manifest.get("iiif_type") == "manifest"
    # assert manifest.get("url") == f"http://localhost:8000/iiif/manifest/{test_data_store.get('manifest')}/"
    assert manifest.get("label") == simple_iiif3_manifest.get("label")
    assert manifest.get("thumbnail") == simple_iiif3_manifest.get("thumbnail")
    assert manifest.get("id") == None
    assert manifest.get("iiif_json") == None
    assert manifest.get("original_id") == None


def test_iiif_store_public_iiif_get_manifest(http_service, simple_iiif3_manifest):
    test_endpoint = f"iiif/manifest/{test_data_store.get('manifest')}"
    status = 200
    response = requests.get(f"{http_service}/{test_endpoint}", headers=test_headers)
    assert response.status_code == status
    response_json = response.json()
    expected_manifest = copy.deepcopy(simple_iiif3_manifest)
    expected_manifest.pop("id")
    manifest_id = response_json.pop("id")
    assert (
        manifest_id
        == f"http://localhost:8000/iiif/manifest/{test_data_store.get('manifest')}/"
    )
    assert response_json == expected_manifest


def test_iiif_store_public_iiif_get_canvas(http_service):
    test_endpoint = f"iiif/canvas/{test_data_store.get('canvas')}"
    status = 200
    response = requests.get(f"{http_service}/{test_endpoint}", headers=test_headers)
    assert response.status_code == status
    response_json = response.json()
    manifest_id = response_json.pop("id")
    assert (
        manifest_id
        == f"http://localhost:8000/iiif/canvas/{test_data_store.get('canvas')}/"
    )


@pytest.mark.skip(reason="Annotations not being created with default IIIF_RESOURCE_TYPES")
def test_iiif_store_public_iiif_get_annotation(http_service):
    test_endpoint = f"iiif/annotation/{test_data_store.get('annotation')}"
    status = 200
    response = requests.get(f"{http_service}/{test_endpoint}", headers=test_headers)
    assert response.status_code == status
    response_json = response.json()
    manifest_id = response_json.pop("id")
    assert (
        manifest_id
        == f"http://localhost:8000/iiif/annotation/{test_data_store.get('annotation')}/"
    )


@pytest.mark.skip(reason="AnnotationPages not being created with default IIIF_RESOURCE_TYPES")
def test_iiif_store_public_iiif_get_annotationpage(http_service):
    test_endpoint = f"iiif/annotationpage/{test_data_store.get('annotationpage')}"
    status = 200
    response = requests.get(f"{http_service}/{test_endpoint}", headers=test_headers)
    assert response.status_code == status
    response_json = response.json()
    manifest_id = response_json.pop("id")
    assert (
        manifest_id
        == f"http://localhost:8000/iiif/annotationpage/{test_data_store.get('annotationpage')}/"
    )


def test_search_service_api_iiif_indexables(http_service):
    app_endpoint = "api/search_service"
    test_endpoint = "indexable"
    status = 200
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    assert response.status_code == status
    response_json = response.json()
    assert response_json.get("count") == 3
    assert response_json.get("next") == None
    assert response_json.get("previous") == None
    assert len(response_json.get("results")) == 3

    for indexable in response_json.get("results"):
        if indexable.get("indexable_text") == "Canvas label":
            assert indexable.get("resource_id") == test_data_store.get("canvas")
            assert indexable.get("type") == "descriptive"
            assert indexable.get("subtype") == "label"
            assert indexable.get("language_iso639_2") == "eng"
        elif indexable.get("indexable_text") == "Manifest label":
            assert indexable.get("resource_id") == test_data_store.get("manifest")
            assert indexable.get("type") == "descriptive"
            assert indexable.get("subtype") == "label"
            assert indexable.get("language_iso639_2") == "eng"
        elif indexable.get("indexable_text") == "Manifest author":
            assert indexable.get("resource_id") == test_data_store.get("manifest")
            assert indexable.get("type") == "metadata"
            assert indexable.get("subtype") == "author"
            assert indexable.get("language_iso639_2") == "eng"
        else:
            assert True == False


def test_iiif_store_api_iiif_delete(http_service):
    test_endpoint = f"iiif/{test_data_store.get('manifest')}"
    status = 204
    response = requests.delete(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    assert response.status_code == status

    status = 404
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    assert response.status_code == status

    test_endpoint = f"iiif/{test_data_store.get('canvas')}"
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    assert response.status_code == status

    test_endpoint = f"iiif/{test_data_store.get('annotation')}"
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    assert response.status_code == status

    test_endpoint = f"iiif/{test_data_store.get('annotationpage')}"
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    assert response.status_code == status

def test_search_service_api_iiif_indexable_deleted(http_service):
    app_endpoint = "api/search_service"
    test_endpoint = "indexable"
    status = 200
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    assert response.status_code == status
    response_json = response.json()
    assert response_json.get("count") == 0
    assert response_json.get("next") == None
    assert response_json.get("previous") == None
    assert len(response_json.get("results")) == 0

