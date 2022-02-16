import copy
import json
import pytest
import requests


app_endpoint = "api/iiif_store"
test_headers = {"Content-Type": "application/json", "Accept": "application/json"}

test_data_store = {}


@pytest.fixture
def simple_multilingual_iiif3_manifest(tests_dir):
    return json.load(
        (tests_dir / "fixtures/simple_multilingual_iiif3_manifest.json").open(encoding="utf-8")
    )


def test_iiif_store_api_multilingual_iiif_create_manifest(http_service, simple_multilingual_iiif3_manifest):
    post_json = {
        "iiif_json": simple_multilingual_iiif3_manifest,
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
    assert len(response_json.get("resources")) == 4
    assert len(response_json.get("relationships")) == 6

    for resource in response_json.get("resources"):
        test_data_store[resource.get("iiif_type")] = resource.get("id")

    manifest_response_json = response_json.get("resources")[0]
    assert manifest_response_json.get("id") is not None
    assert manifest_response_json.get("iiif_type") == "manifest"
    assert manifest_response_json.get("original_id") == simple_multilingual_iiif3_manifest.get("id")
    assert manifest_response_json.get("iiif_json").get(
        "id"
    ) != simple_multilingual_iiif3_manifest.get("id")
    assert manifest_response_json.get("label") == simple_multilingual_iiif3_manifest.get("label")
    assert (
        manifest_response_json.get("iiif_json").get("id")
        == f"http://localhost:8000/iiif/manifest/{test_data_store.get('manifest')}/"
    )
    expected_manifest = copy.deepcopy(simple_multilingual_iiif3_manifest)
    expected_manifest.pop("id")
    manifest_response_json.get("iiif_json").pop("id")

    assert manifest_response_json.get("iiif_json") == expected_manifest


def test_iiif_store_api_multilingual_iiif_get_manifest(http_service, simple_multilingual_iiif3_manifest):
    test_endpoint = f"iiif/{test_data_store.get('manifest')}"
    status = 200
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    assert response.status_code == status
    response_json = response.json()
    assert response_json.get("id") == test_data_store.get("manifest")
    assert response_json.get("iiif_type") == "manifest"
    assert response_json.get("original_id") == simple_multilingual_iiif3_manifest.get("id")
    assert response_json.get("label") == simple_multilingual_iiif3_manifest.get("label")
    assert response_json.get("thumbnail") == simple_multilingual_iiif3_manifest.get("thumbnail")
    expected_manifest = copy.deepcopy(simple_multilingual_iiif3_manifest)
    expected_manifest.pop("id")
    manifest_id = response_json.get("iiif_json").pop("id")
    assert (
        manifest_id
        == f"http://localhost:8000/iiif/manifest/{test_data_store.get('manifest')}/"
    )
    assert response_json.get("iiif_json") == expected_manifest


def test_iiif_store_public_multilingual_iiif_get_manifest(http_service, simple_multilingual_iiif3_manifest):
    test_endpoint = f"iiif/manifest/{test_data_store.get('manifest')}"
    status = 200
    response = requests.get(f"{http_service}/{test_endpoint}", headers=test_headers)
    assert response.status_code == status
    response_json = response.json()
    expected_manifest = copy.deepcopy(simple_multilingual_iiif3_manifest)
    expected_manifest.pop("id")
    manifest_id = response_json.pop("id")
    assert (
        manifest_id
        == f"http://localhost:8000/iiif/manifest/{test_data_store.get('manifest')}/"
    )
    assert response_json == expected_manifest


def test_search_service_api_multilingual_iiif_indexables(http_service):
    app_endpoint = "api/search_service"
    test_endpoint = "indexables"
    status = 200
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    assert response.status_code == status
    response_json = response.json()
    assert response_json.get("count") == 9
    assert response_json.get("next") == None
    assert response_json.get("previous") == None
    assert len(response_json.get("results")) == 9

    for indexable in response_json.get("results"):
        if indexable.get("indexable_text") == "Canvas label":
            assert indexable.get("resource_id") == test_data_store.get("canvas")
            assert indexable.get("type") == "descriptive"
            assert indexable.get("subtype") == "label"
            assert indexable.get("language_iso639_2") == "eng"
        elif indexable.get("indexable_text") == "Canvas-Etikett":
            assert indexable.get("resource_id") == test_data_store.get("canvas")
            assert indexable.get("type") == "descriptive"
            assert indexable.get("subtype") == "label"
            assert indexable.get("language_iso639_2") == "deu"
        elif indexable.get("indexable_text") == "Libellé du toile":
            assert indexable.get("resource_id") == test_data_store.get("canvas")
            assert indexable.get("type") == "descriptive"
            assert indexable.get("subtype") == "label"
            assert indexable.get("language_iso639_2") == "fra"


        elif indexable.get("indexable_text") == "Manifest label":
            assert indexable.get("resource_id") == test_data_store.get("manifest")
            assert indexable.get("type") == "descriptive"
            assert indexable.get("subtype") == "label"
            assert indexable.get("language_iso639_2") == "eng"
        elif indexable.get("indexable_text") == "Manifestetikett":
            assert indexable.get("resource_id") == test_data_store.get("manifest")
            assert indexable.get("type") == "descriptive"
            assert indexable.get("subtype") == "label"
            assert indexable.get("language_iso639_2") == "deu"
        elif indexable.get("indexable_text") == "Libellé du manifeste":
            assert indexable.get("resource_id") == test_data_store.get("manifest")
            assert indexable.get("type") == "descriptive"
            assert indexable.get("subtype") == "label"
            assert indexable.get("language_iso639_2") == "fra"

        elif indexable.get("indexable_text") == "Manifest author":
            assert indexable.get("resource_id") == test_data_store.get("manifest")
            assert indexable.get("type") == "metadata"
            assert indexable.get("subtype") == "author"
            assert indexable.get("language_iso639_2") == "eng"
        elif indexable.get("indexable_text") == "Manifester urheber":
            assert indexable.get("resource_id") == test_data_store.get("manifest")
            assert indexable.get("type") == "metadata"
            assert indexable.get("subtype") == "urheber"
            assert indexable.get("language_iso639_2") == "deu"
        elif indexable.get("indexable_text") == "Auteur du manifeste":
            assert indexable.get("resource_id") == test_data_store.get("manifest")
            assert indexable.get("type") == "metadata"
            assert indexable.get("subtype") == "auteur"
            assert indexable.get("language_iso639_2") == "fra"
        else:
            assert True == False


def test_iiif_store_api_multilingual_iiif_delete(http_service):
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


def test_search_service_api_multilingual_iiif_indexable_deleted(http_service):
    app_endpoint = "api/search_service"
    test_endpoint = "indexables"
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

