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
        f"{http_service}/{app_endpoint}/{test_endpoint}/", headers=test_headers
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
            f"{http_service}/{app_endpoint}/{test_endpoint}/",
            headers=test_headers,
            json=post_json,
        )
        assert response.status_code == status
        response_json = response.json()
        assert response_json.get("resources") is not None
        assert response_json.get("relationships") is not None
        test_data_store["manifest_uuids"].append(
            response_json.get("resources")[0].get("id")
        )


def test_iiif_store_api_search_populated(http_service):
    test_endpoint = "search"
    status = 200
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}/", headers=test_headers
    )
    assert response.status_code == status
    response_json = response.json()
    assert response_json.get("count") == 10  # 1 manifest, 9 canvases
    assert len(response_json.get("results")) == 10


def test_iiif_store_api_search_simple_query(http_service):
    test_endpoint = "search"
    status = 200
    post_json = {"fulltext": "heron"}
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}/",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) > 0


def test_iiif_store_api_search_simple_query_no_match(http_service):
    test_endpoint = "search"
    status = 200
    post_json = {"fulltext": "philo"}
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}/",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == 0


def test_iiif_store_api_search_simple_query_rank(http_service):
    test_endpoint = "search"
    status = 200
    post_json = {"fulltext": "heron"}
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}/",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert (
        int(response_json["results"][0].get("rank", 0)) > 0
    )  # There is a non-zero rank


def test_iiif_store_api_search_simple_query_snippet(http_service):
    test_endpoint = "search"
    status = 200
    post_json = {"fulltext": "heron"}
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}/",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert "<b>Heron</b>" in response_json["results"][0].get("snippet", None)


def test_iiif_store_api_search_facet_query(http_service):
    test_endpoint = "search"
    status = 200
    post_json = {
        "facets": [{"type": "metadata", "subtype": "author", "value": "Ktesibios"}]
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}/",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == 1


def test_iiif_store_api_search_another_facet_query(http_service):
    test_endpoint = "search"
    status = 200
    post_json = {
        "facets": [
            {"type": "metadata", "subtype": "urheber", "value": "Heron von Alexandria"}
        ]
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}/",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == 3


def test_iiif_store_api_search_facet_query_wrong_key(http_service):
    """
    Looking for a value, but it's stored in a different key
    """
    test_endpoint = "search"
    status = 200
    post_json = {
        "facets": [{"type": "metadata", "subtype": "language", "value": "Pictish"}]
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}/",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == 0


def test_iiif_store_api_search_resource_query(http_service):
    test_endpoint = "search"
    status = 200
    post_json = {  # Partial match on label, should match against "Another"
        "resource_filters": [
            {
                "value": {"en": ["Pneumatica"]},
                "field": "label",
                "operator": "contains",
                "resource_class": "iiifresource",
            }
        ],
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}/",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == 2


def test_iiif_store_api_search_resource_query_no_match(http_service):
    test_endpoint = "search"
    status = 200
    post_json = {
        "resource_filters": [
            {
                "value": "something",
                "field": "label",
                "operator": "icontains",
                "resource_class": "jsonresource",
            }
        ],
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}/",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == 0


def test_iiif_store_api_search_resource_query_no_resourceclass(http_service):
    """
    THis will 500 as there is no `foo` model defined in the application
    """
    test_endpoint = "search"
    status = 500
    post_json = {
        "resource_filters": [
            {
                "value": "other",
                "field": "label",
                "operator": "icontains",
                "resource_class": "foo",
            }
        ],
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}/",
        json=post_json,
        headers=test_headers,
    )
    assert response.status_code == status


def test_iiif_store_api_iiif_delete_manifests_for_search(
    http_service, iiif3_search_manifests
):
    test_endpoint = "iiif"
    for manifest_id in test_data_store.get("manifest_uuids"):
        test_endpoint = f"iiif/{manifest_id}"
        status = 204
        response = requests.delete(
            f"{http_service}/{app_endpoint}/{test_endpoint}/", headers=test_headers
        )
        assert response.status_code == status
