import copy
import json
import pytest
import requests

MOCK_CANONICAL_HOSTNAME = "http://iiif-discovery-test.org"


class IIIF3StoreTestData(object):
    manifest_uuid = None


test_data = IIIF3StoreTestData()
def test_api_stored_iiif3_resource_public_get(http_service, iiif_store_manifest):
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    manifest_url = http_service + f"/iiif/manifest/{test_data.manifest_uuid}"
    result = requests.get(url=manifest_url, headers=headers)
    j = result.json()
    assert result.status_code == 200
    assert (
        j.pop("id")
        == MOCK_CANONICAL_HOSTNAME + f"/iiif/manifest/{test_data.manifest_uuid}"
    )
    expected_manifest = copy.deepcopy(iiif_store_manifest)
    expected_manifest.pop("id")
    assert j == expected_manifest


def test_api_stored_iiif3_resource_api_update(
    http_service, test_api_auth, iiif_store_manifest
):
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    iiif_store_manifest["metadata"].append(
        {"label": {"en": ["author"]}, "value": {"en": ["update test indexing"]}}
    )
    post_json = {
        "iiif_json": iiif_store_manifest,
        "iiif_type": "Manifest",
    }

    result = requests.put(
        url=http_service + f"/api/iiif_store/resource/{test_data.manifest_uuid}/",
        json=post_json,
        headers=headers,
        auth=test_api_auth,
    )
    j = result.json()
    assert j.get("id") == test_data.manifest_uuid
    assert j.get("iiif_type") == post_json.get("iiif_type").lower()
    assert j.get("original_id") == iiif_store_manifest.get("id")
    assert j.get("iiif_json").get("id") != iiif_store_manifest.get("id")
    assert j.get("label") == iiif_store_manifest.get("label")
    assert j.get("thumbnail") == iiif_store_manifest.get("thumbnail")
    assert (
        j.get("iiif_json").get("id")
        == MOCK_CANONICAL_HOSTNAME + f"/iiif/manifest/{test_data.manifest_uuid}"
    )
    expected_manifest = copy.deepcopy(iiif_store_manifest)
    expected_manifest.pop("id")
    j.get("iiif_json").pop("id")
    assert j.get("iiif_json") == expected_manifest


def test_api_stored_iiif3_resource_api_delete(http_service, test_api_auth):
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    result = requests.delete(
        url=http_service + f"/api/iiif_store/resource/{test_data.manifest_uuid}/",
        headers=headers,
        auth=test_api_auth,
    )
    assert result.status_code == 204
