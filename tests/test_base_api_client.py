# -*- coding: utf-8 -*-
import requests
import pytest
import mock

from dmapiclient.base import BaseAPIClient
from dmapiclient import HTTPError, InvalidResponse
from dmapiclient.errors import REQUEST_ERROR_STATUS_CODE
from dmapiclient.errors import REQUEST_ERROR_MESSAGE
from dmapiclient.exceptions import ImproperlyConfigured


@pytest.yield_fixture
def raw_rmock():
    with mock.patch('dmapiclient.base.requests.request') as rmock:
        yield rmock


@pytest.fixture
def base_client():
    return BaseAPIClient('http://baseurl', 'auth-token', True)


class TestBaseApiClient(object):
    def test_connection_error_raises_api_error(self, base_client, raw_rmock):
        raw_rmock.side_effect = requests.exceptions.ConnectionError(
            None
        )
        with pytest.raises(HTTPError) as e:
            base_client._request("GET", '/')

        assert e.value.message == REQUEST_ERROR_MESSAGE
        assert e.value.status_code == REQUEST_ERROR_STATUS_CODE

    def test_http_error_raises_api_error(self, base_client, rmock):
        rmock.request(
            "GET",
            "http://baseurl/",
            text="Internal Error",
            status_code=500)

        with pytest.raises(HTTPError) as e:
            base_client._request("GET", '/')

        assert e.value.message == REQUEST_ERROR_MESSAGE
        assert e.value.status_code == 500

    def test_non_2xx_response_raises_api_error(self, base_client, rmock):
        rmock.request(
            "GET",
            "http://baseurl/",
            json={"error": "Not found"},
            status_code=404)

        with pytest.raises(HTTPError) as e:
            base_client._request("GET", '/')

        assert e.value.message == "Not found"
        assert e.value.status_code == 404

    def test_invalid_json_raises_api_error(self, base_client, rmock):
        rmock.request(
            "GET",
            "http://baseurl/",
            text="Internal Error",
            status_code=200)

        with pytest.raises(InvalidResponse) as e:
            base_client._request("GET", '/')

        assert e.value.message == "No JSON object could be decoded"
        assert e.value.status_code == 200

    def test_user_agent_is_set(self, base_client, rmock):
        rmock.request(
            "GET",
            "http://baseurl/",
            json={},
            status_code=200)

        base_client._request('GET', '/')

        assert rmock.last_request.headers.get("User-Agent").startswith("DM-API-Client/")

    def test_request_always_uses_base_url_scheme(self, base_client, rmock):
        rmock.request(
            "GET",
            "http://baseurl/path/",
            json={},
            status_code=200)

        base_client._request('GET', 'https://host/path/')
        assert rmock.called

    def test_null_api_throws(self):
        bad_client = BaseAPIClient(None, 'auth-token', True)
        with pytest.raises(ImproperlyConfigured):
            bad_client._request('GET', '/anything')