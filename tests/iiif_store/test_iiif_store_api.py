import copy
import json
import pytest
import requests


app_endpoint = "api/iiif_store"
test_headers = {"Content-Type": "application/json", "Accept": "application/json"}

test_data_store = {}


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


def test_iiif_store_api_iiif_create_manifest(http_service, test_iiif3_manifest):
    post_json = {
        "iiif_json": test_iiif3_manifest,
        "iiif_type": "Manifest",
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
    assert response_json.get("id") is not None
    test_data_store["test_manifest_uuid"] = response_json.get("id")
    assert response_json.get("iiif_type") == post_json.get("iiif_type").lower()
    assert response_json.get("original_id") == test_iiif3_manifest.get("id")
    assert response_json.get("iiif_json").get("id") != test_iiif3_manifest.get("id")
    assert response_json.get("label") == test_iiif3_manifest.get("label")
    assert (
        response_json.get("iiif_json").get("id")
        == f"http://localhost:8000/iiif/manifest/{test_data_store.get('test_manifest_uuid')}/"
    )
    expected_manifest = copy.deepcopy(test_iiif3_manifest)
    expected_manifest.pop("id")
    response_json.get("iiif_json").pop("id")
    assert response_json.get("iiif_json") == expected_manifest


def test_iiif_store_api_iiif_list(http_service, test_iiif3_manifest):
    test_endpoint = "iiif"
    status = 200
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    assert response.status_code == status
    response_json = response.json()
    assert response_json.get("count") == 1
    assert response_json.get("next") == None
    assert response_json.get("previous") == None
    assert len(response_json.get("results")) == 1

    manifest = response_json["results"][0]
    assert manifest.get("id") == test_data_store.get("test_manifest_uuid")
    assert manifest.get("iiif_type") == "manifest"
    assert manifest.get("original_id") == test_iiif3_manifest.get("id")
    assert manifest.get("label") == test_iiif3_manifest.get("label")
    assert manifest.get("thumbnail") == test_iiif3_manifest.get("thumbnail")
    assert manifest.get("iiif_json") == None


def test_iiif_store_api_iiif_get(http_service, test_iiif3_manifest):
    test_endpoint = f"iiif/{test_data_store.get('test_manifest_uuid')}"
    status = 200
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    assert response.status_code == status
    response_json = response.json()
    assert response_json.get("id") == test_data_store.get("test_manifest_uuid")
    assert response_json.get("iiif_type") == "manifest"
    assert response_json.get("original_id") == test_iiif3_manifest.get("id")
    assert response_json.get("label") == test_iiif3_manifest.get("label")
    assert response_json.get("thumbnail") == test_iiif3_manifest.get("thumbnail")
    expected_manifest = copy.deepcopy(test_iiif3_manifest)
    expected_manifest.pop("id")
    manifest_id = response_json.get("iiif_json").pop("id")
    assert (
        manifest_id
        == f"http://localhost:8000/iiif/manifest/{test_data_store.get('test_manifest_uuid')}/"
    )
    assert response_json.get("iiif_json") == expected_manifest


def test_iiif_store_public_iiif_list(http_service, test_iiif3_manifest):
    test_endpoint = "iiif"
    status = 200
    response = requests.get(f"{http_service}/{test_endpoint}", headers=test_headers)
    assert response.status_code == status
    response_json = response.json()
    assert response_json.get("count") == 1
    assert response_json.get("next") == None
    assert response_json.get("previous") == None
    assert len(response_json.get("results")) == 1

    manifest = response_json["results"][0]
    assert manifest.get("iiif_type") == "manifest"
    # assert manifest.get("url") == f"http://localhost:8000/iiif/manifest/{test_data_store.get('test_manifest_uuid')}/"
    assert manifest.get("label") == test_iiif3_manifest.get("label")
    assert manifest.get("thumbnail") == test_iiif3_manifest.get("thumbnail")
    assert manifest.get("id") == None
    assert manifest.get("iiif_json") == None
    assert manifest.get("original_id") == None


def test_iiif_store_public_iiif_get(http_service, test_iiif3_manifest):
    test_endpoint = f"iiif/manifest/{test_data_store.get('test_manifest_uuid')}"
    status = 200
    response = requests.get(f"{http_service}/{test_endpoint}", headers=test_headers)
    assert response.status_code == status
    response_json = response.json()
    expected_manifest = copy.deepcopy(test_iiif3_manifest)
    expected_manifest.pop("id")
    manifest_id = response_json.pop("id")
    assert (
        manifest_id
        == f"http://localhost:8000/iiif/manifest/{test_data_store.get('test_manifest_uuid')}/"
    )
    assert response_json == expected_manifest


def test_iiif_store_api_iiif_delete(http_service):
    test_endpoint = f"iiif/{test_data_store.get('test_manifest_uuid')}"
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
