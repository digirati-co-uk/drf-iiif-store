import copy
import json
import pytest
import requests


app_endpoint = "api/iiif_store"
test_headers = {"Content-Type": "application/json", "Accept": "application/json"}

test_data_store = {"manifest_uuids": []}


@pytest.fixture
def iiif3_search_manifests(tests_dir):
    iiif3_manifests = {}
    for iiif3_file in (tests_dir / "fixtures/search/iiif3/").iterdir():
        iiif3_manifests[iiif3_file.name] = json.load(iiif3_file.open(encoding="utf-8"))
    return iiif3_manifests


def test_iiif_store_api_root_get(http_service):
    status = 200
    response = requests.get(f"{http_service}/{app_endpoint}", headers=test_headers)
    assert response.status_code == status


def test_iiif_store_api_search_empty(http_service):
    test_endpoint = "search"
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


def test_iiif_store_api_iiif_create_manifests_for_search(
    http_service, iiif3_search_manifests
):
    test_endpoint = "iiif"
    status = 201
    for manifest_json in iiif3_search_manifests.values():
        post_json = {
            "iiif_json": manifest_json,
        }
        response = requests.post(
            f"{http_service}/{app_endpoint}/{test_endpoint}",
            headers=test_headers,
            json=post_json,
        )
        assert response.status_code == status
        response_json = response.json()
        assert response_json.get("resources") is not None
        assert response_json.get("relationships") is not None
        test_data_store["manifest_uuids"].append(response_json.get("resources")[0].get("id"))


def test_iiif_store_api_search_populated(http_service):
    test_endpoint = "search"
    status = 200
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    assert response.status_code == status
    response_json = response.json()
    assert response_json.get("count") == 8
    assert len(response_json.get("results")) == 8

def test_iiif_store_api_iiif_delete_manifests_for_search(
    http_service, iiif3_search_manifests
):
    test_endpoint = "iiif"
    for manifest_id in test_data_store.get("manifest_uuids"):
        test_endpoint = f"iiif/{manifest_id}"
        status = 204
        response = requests.delete(
            f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
        )
        assert response.status_code == status
