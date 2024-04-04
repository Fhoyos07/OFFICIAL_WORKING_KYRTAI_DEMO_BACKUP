import pytest
from rest_framework.test import APIRequestFactory
from apps.web.views import CompanyViewSet, CaseViewSet
from .fixtures import *



def _assert_cases_list(response, expected_case_states: set[str]):
    assert response.status_code == 200
    assert response.data['count'] == len(expected_case_states)
    assert {r['state_code'] for r in response.data['results']} == expected_case_states


def test_cases(api_request_factory: APIRequestFactory, cases: dict[str, Case]):
    view = CaseViewSet.as_view({'get': 'list'})
    request = api_request_factory.get("/cases/")
    response = view(request)

    # assert
    _assert_cases_list(response, expected_case_states={'NY', 'CT'})


def test_cases_filter_state(api_request_factory: APIRequestFactory, cases: dict[str, Case]):
    view = CaseViewSet.as_view({'get': 'list'})
    request = api_request_factory.get("/cases/", data=dict(
        state_code='NY'
    ))
    response = view(request)

    # assert
    _assert_cases_list(response, expected_case_states={'NY'})


def test_cases_filter_date_from(api_request_factory: APIRequestFactory, cases: dict[str, Case]):
    view = CaseViewSet.as_view({'get': 'list'})
    request = api_request_factory.get("/cases/", data=dict(
        date_from='2024-01-01'
    ))
    response = view(request)

    # assert
    _assert_cases_list(response, expected_case_states={'NY'})


def test_cases_filter_date_to(api_request_factory: APIRequestFactory, cases: dict[str, Case]):
    view = CaseViewSet.as_view({'get': 'list'})
    request = api_request_factory.get("/cases/", data=dict(
        date_to='2023-12-31'
    ))
    response = view(request)

    # assert
    _assert_cases_list(response, expected_case_states={'CT'})


def test_cases_filter_court(api_request_factory: APIRequestFactory, cases: dict[str, Case]):
    view = CaseViewSet.as_view({'get': 'list'})
    request = api_request_factory.get("/cases/", data=dict(
        court='Supreme'
    ))
    response = view(request)

    # assert
    _assert_cases_list(response, expected_case_states={'NY'})


def test_cases_filter_case_type(api_request_factory: APIRequestFactory, cases: dict[str, Case]):
    view = CaseViewSet.as_view({'get': 'list'})
    request = api_request_factory.get("/cases/", data=dict(
        case_type='Civil'
    ))
    response = view(request)

    # assert
    _assert_cases_list(response, expected_case_states={'NY'})


def test_cases_filter_caption(api_request_factory: APIRequestFactory, cases: dict[str, Case]):
    view = CaseViewSet.as_view({'get': 'list'})
    request = api_request_factory.get("/cases/", data=dict(
        caption='1'
    ))
    response = view(request)

    # assert
    _assert_cases_list(response, expected_case_states={'NY'})
