import copy
import json
import pytest
import requests


app_endpoint = 'api/iiif_store'
test_headers = {"Content-Type": "application/json", "Accept": "application/json"}


def test_resource_list(http_service):
    """ 
        """
    test_endpoint = "resource"
    status = 200
    response = requests.get(f"{http_service}/{app_endpoint}/{test_endpoint}", headers=test_headers)
    resp_data = response.json()
    assert response.status_code == status
