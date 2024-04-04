from rest_framework.test import APIRequestFactory
from apps.web.models import Case
from .conftest import _make_request_companies_list


def test_companies_unauthorized(cases: dict[str, Case]):
    unauthorized_api_request_factory = APIRequestFactory()
    response = _make_request_companies_list(unauthorized_api_request_factory)
    assert response.status_code == 403


def test_cases_authorized(api_key: str, cases: dict[str, Case]):
    authorized_api_request_factory = APIRequestFactory(headers={'X-API-KEY': api_key})
    response = _make_request_companies_list(authorized_api_request_factory)
    assert response.status_code == 200
