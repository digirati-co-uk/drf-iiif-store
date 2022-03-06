import copy
import json
import pytest
import requests
from ..utils import is_responsive_404

app_endpoint = "api/search_service"
test_headers = {"Content-Type": "application/json", "Accept": "application/json"}
test_data_store = {}


def test_json_resource_create(http_service):
    """ """
    test_endpoint = "json_resource"
    status = 201
    post_json = {
        "label": "A Test Resource",
        "data": {"key_1": "Value 1", "key_2": "Value 2"},
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert response_json.get("label") == post_json.get("label")
    assert response_json.get("data") == post_json.get("data")
    assert response_json.get("created") is not None
    assert response_json.get("modified") is not None
    assert response_json.get("id") is not None
    test_data_store["json_resource_id"] = response_json.get("id")


def test_json_resource_get(http_service):
    """ """
    test_endpoint = "json_resource"
    status = 200
    resource_id = test_data_store.get("json_resource_id")
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}/{resource_id}",
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert response_json.get("id") == resource_id


def test_json_resource_indexables_creation(http_service):
    """ """
    test_endpoint = "indexables"
    status = 200
    resource_id = test_data_store.get("json_resource_id")
    response = requests.get(
        f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == 3
    for indexable in response_json.get("results"):
        assert indexable.get("resource_id") == resource_id


def test_json_resource_simple_query(http_service):
    test_endpoint = "json_search"
    status = 200
    post_json = {"fulltext": "resource"}
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) > 0


def test_json_resource_simple_query_no_match(http_service):
    test_endpoint = "json_search"
    status = 200
    post_json = {"fulltext": "digirati"}
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == 0


def test_json_resource_simple_query_rank(http_service):
    test_endpoint = "json_search"
    status = 200
    post_json = {"fulltext": "resource"}
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert (
        int(response_json["results"][0].get("rank", 0)) > 0
    )  # There is a non-zero rank


def test_json_resource_simple_query_snippet(http_service):
    test_endpoint = "json_search"
    status = 200
    post_json = {"fulltext": "resource"}
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert "<b>Resource</b>" in response_json["results"][0].get("snippet", None)


def test_json_resource_facet_query(http_service):
    test_endpoint = "json_search"
    status = 200
    post_json = {
        "facets": [{"type": "descriptive", "subtype": "key_1", "value": "Value 1"}]
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == 1


def test_json_another_resource_create(http_service):
    """ """
    test_endpoint = "json_resource"
    status = 201
    post_json = {
        "label": "Another item",
        "data": {"key_1": "Value 1", "key_3": "Value 3"},
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    assert response.status_code == status


def test_json_resource_another_facet_query(http_service):
    test_endpoint = "json_search"
    status = 200
    post_json = {
        "facets": [{"type": "descriptive", "subtype": "key_1", "value": "Value 1"}]
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == 2


def test_json_resource_facet_query_wrong_key(http_service):
    """
    Looking for a value, but it's stored in a different key
    """
    test_endpoint = "json_search"
    status = 200
    post_json = {
        "facets": [{"type": "descriptive", "subtype": "key_3", "value": "Value 1"}]
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == 0


def test_json_resource_simple_query_data_key(http_service):
    test_endpoint = "json_search"
    post_json = {"fulltext": "Value 3"}
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert len(response_json.get("results")) == 1
    assert "<b>Value</b>" in response_json["results"][0].get("snippet", None)


def test_json_resource_simple_query_data_key_broader(http_service):
    test_endpoint = "json_search"
    post_json = {"fulltext": "Value"}
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert len(response_json.get("results")) == 2  # No longer one per hit, but one per resource
    assert "<b>Value</b>" in response_json["results"][0].get("snippet", None)


def test_json_resource_resource_query(http_service):
    test_endpoint = "json_search"
    status = 200
    post_json = {  # Partial match on label, should match against "Another"
        "resource_filters": [
            {
                "value": "other",
                "field": "label",
                "operator": "icontains",
                "resource_class": "jsonresource",
            }
        ],
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == 1


def test_json_resource_resource_query_no_match(http_service):
    test_endpoint = "json_search"
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
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == 0


def test_json_resource_resource_query_no_resourceclass(http_service):
    """
    THis will 500 as there is no `foo` model defined in the application
    """
    test_endpoint = "json_search"
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
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    assert response.status_code == status


def test_json_html_resource_create(http_service):
    """ """
    test_endpoint = "json_resource"
    status = 201
    post_json = {
        "label": "220_0833_fol4v_na_en_ad_pr",
        "data": {
            "transcript": "<p>the one with the wind jewel, the one with the turkey blood design, or the one with the"
            " whirlpool design, the one with the smoking mirror. </p>\n<p>All these various things they "
            "presented to [the Spaniards. These] gave them gifts in return. They offered them green and"
            " yellow necklaces which resembled amber.[^5] </p>\n<p>And when they had taken [the gift], "
            "when they had seen it, much did they marvel. </p>\n<p>And [the Spaniards] addressed them; "
            'they said to them: "Go! For the time being we depart for Castile. We shall not tarry in '
            'going to reach Mexico." </p>\n<p>Thereupon [the Spaniards] went. Thereupon also [the others]'
            " came back; they turned back. </p>\n<p>And when they had come to emerge on dry land, then"
            " they went direct to Mexico. Day by day, night by "
            'night<a href="_Ibid_.:" title="_en vn dia, y en vna noche_.">^6</a> they traveled in '
            "order to come to warn Moctezuma, in order to come to tell him exactly of its "
            "circumstances; they came to notify him.[^7] Their goods had come to be what they had gone"
            ' to receive. </p>\n<p>And thereupon they addressed him: "O our lord, O my noble youth, '
            "may thou destroy us. For behold what we have seen, behold what we have done, there where"
            "thy grandfathers stand guard for thee before the ocean. For we went to see our lords the"
            " gods in the midst of the water. All thy capes we went to give them. And behold their "
            "noble goods which they gave us.</p>\n"
            '<p>[^5]: Spanish text: "<em>los españoles dieron a los indios cuētas de vidrio, '
            'vnas verdes y otras amarillas</em>."</p>\n<p>[^7]: Seler, <em>Einige Kapitel</em>, '
            'p. 458, has <em>ivel ioca</em>, translated "first of all." '
            "Garibay (Sahagún, Garibay ed., Vol. IV, p. 84) translates "
            'the passage thus: "<em>Día y noche vinieron caminando para comunicar a '
            'Motecuzoma, para decirle y darle a saber con verdad lo que él pudiera saber</em>." </p>',
            "additional": "The emperor was known as Moctezuma in some texts.",
        },
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    assert response.status_code == status


def test_json_resource_resource_query_by_label(http_service):
    test_endpoint = "json_search"
    status = 200
    post_json = {
        "resource_filters": [
            {
                "value": "220_0833_fol4v_na_en_ad_pr",
                "field": "label",
                "operator": "exact",
                "resource_class": "jsonresource",
            }
        ],
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == 1


def test_json_resource_resource_query_by_label_missing(http_service):
    test_endpoint = "json_search"
    status = 200
    post_json = {
        "resource_filters": [
            {
                "value": "I don't exist",
                "field": "label",
                "operator": "exact",
                "resource_class": "jsonresource",
            }
        ],
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == 0


def test_json_resource_resource_query_by_list(http_service):
    test_endpoint = "json_search"
    status = 200
    post_json = {
        "resource_filters": [
            {
                "value": ["220_0833_fol4v_na_en_ad_pr"],
                "field": "label",
                "operator": "in",
                "resource_class": "jsonresource",
            }
        ],
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert len(response_json.get("results")) == 1


def test_json_resource_fulltext_phrase_search(http_service):
    test_endpoint = "json_search"
    post_json = {
        "fulltext": "turkey blood",
        "search_type": "phrase",
        "search_language": "english",
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert len(response_json.get("results")) == 1
    assert "<b>turkey</b> <b>blood</b>" in response_json["results"][0].get(
        "snippet", None
    )
    assert response_json["results"][0]["rank"] > 0


def test_json_resource_fulltext_search_multiples(http_service):
    """
    Check that a search where a single indexable matches multiple times
    that the rank for that result is going ot be higher than when the term only
    matches once
    """
    test_endpoint = "json_search"
    post_json = {"fulltext": "behold"}
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert len(response_json.get("results")) == 1
    assert "<b>behold</b>" in response_json["results"][0].get("snippet", None)
    assert response_json["results"][0]["rank"] > 1


def test_json_resource_fulltext_search_single(http_service):
    test_endpoint = "json_search"
    post_json = {"fulltext": "grandfathers"}
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert len(response_json.get("results")) == 1
    assert "<b>grandfathers</b>" in response_json["results"][0].get("snippet", None)
    assert response_json["results"][0]["rank"] == 1.0


def test_json_resource_fulltext_search_multiple_indexables(http_service):
    """
    Validate that annotation works because we get 1 result, not 2.
    """
    test_endpoint = "json_search"
    post_json = {"fulltext": "moctezuma"}
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert (
        len(response_json.get("results")) == 1
    )
    assert "<b>Moctezuma</b>" in response_json["results"][0].get("snippet", None)
    assert response_json["results"][0]["rank"] == 1.0


def test_nested_json_resource_create(http_service):
    """ """
    test_endpoint = "json_resource/create_nested"
    status = 201
    post_json = {
        "label": "Manifest Resource",
        "data": {"iiif_type": "manifest", "volume": "Volume 3"},
        "child_resources": [
            {
                "label": "Vol 3: Canvas 1",
                "data": {
                    "iiif_type": "canvas",
                    "transcript": "The quick brown fox jumped over the lazy dog.",
                },
            },
            {
                "label": "Vol 3: Canvas 2",
                "data": {
                    "iiif_type": "canvas",
                    "transcript": "Round the rugged rock the ragged rascal ran.",
                },
            },
        ],
    }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert response.status_code == status
    assert isinstance(response_json, list)
    assert response_json[0]["data"]["iiif_type"] == "manifest"
    assert sorted(list(set([x["data"]["iiif_type"] for x in response_json if x.get("data")]))) == ["canvas", "manifest"]
    assert all([x.get("target_id") is not None for x in response_json if not x.get("data")])
    assert all([x.get("source_id") is not None for x in response_json if not x.get("data")])


def test_json_resource_fulltext_nested_canvas(http_service):
    """
    """
    test_endpoint = "json_search"
    post_json = {"fulltext": "rugged",
                 }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert (
        len(response_json.get("results")) == 1
    )
    assert "<b>rugged</b>" in response_json["results"][0].get("snippet", None)
    assert response_json["results"][0]["rank"] == 1.0
    assert response_json["results"][0]["data"]["iiif_type"] == "canvas"


# @pytest.mark.skip("This won't work until the facet and fulltext search is fixed")
def test_json_resource_fulltext_nested_canvas_facets(http_service):
    """
    """
    test_endpoint = "json_search"
    post_json = {"fulltext": "rugged",
                 "facets": [{"type": "descriptive", "subtype": "iiif_type", "value": "canvas"}]
                 }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert (
        len(response_json.get("results")) == 1
    )
    assert "<b>rugged</b>" in response_json["results"][0].get("snippet", None)
    assert response_json["results"][0]["rank"] == 1.0


def test_json_resource_fulltext_nested_canvas_facet_on_without_query(http_service):
    """
    """
    test_endpoint = "json_search"
    post_json = {"fulltext": "rugged",
                 "facets": [{"type": "descriptive", "subtype": "label", "value": "Volume 3"}]
                 }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert (
        len(response_json.get("results")) == 0
    )


def test_json_resource_fulltext_nested_canvas_facet_on_with_query(http_service):
    """
    """
    test_endpoint = "json_search"
    post_json = {"fulltext": "rugged",
                 "facets": [{"type": "descriptive", "subtype": "volume", "value": "Volume 3"}],
                 "facet_on": {"data__iiif_type": "manifest", "relationship_targets__type": "part_of"},
                 }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert (
        len(response_json.get("results")) == 1
    )
    assert "<b>rugged</b>" in response_json["results"][0].get("snippet", None)
    assert response_json["results"][0]["rank"] == 1.0


def test_json_resource_fulltext_nested_canvas_facet_on_no_match(http_service):
    """
    """
    test_endpoint = "json_search"
    post_json = {"fulltext": "rugged",
                 "facets": [{"type": "descriptive", "subtype": "volume", "value": "Volume 11"}],
                 "facet_on": {"data__iiif_type": "manifest", "relationship_targets__type": "part_of"},
                 }
    response = requests.post(
        f"{http_service}/{app_endpoint}/{test_endpoint}",
        json=post_json,
        headers=test_headers,
    )
    response_json = response.json()
    assert (
        len(response_json.get("results")) == 0
    )
