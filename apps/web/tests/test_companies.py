from apps.web.models import Company

from rest_framework.test import APIRequestFactory
from .conftest import _make_request_companies_list


def test_companies(api_request_factory: APIRequestFactory, companies: dict[str, Company]):
    # act
    response = _make_request_companies_list(api_request_factory)

    # assert
    _assert_companies_list(response, expected_company_names={'First', 'Second'})


def test_companies_filter_name(api_request_factory: APIRequestFactory, companies: dict[str, Company]):
    # act
    response = _make_request_companies_list(api_request_factory, data=dict(
        name='first'
    ))

    # assert
    _assert_companies_list(response, expected_company_names={'First'})


def _assert_companies_list(response, expected_company_names: set[str]):
    assert response.status_code == 200
    assert response.data['count'] == len(expected_company_names)
    assert {c['name'] for c in response.data['results']} == expected_company_names
