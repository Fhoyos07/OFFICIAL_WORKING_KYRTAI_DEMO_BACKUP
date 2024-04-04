from rest_framework.test import APIRequestFactory
from apps.web.models import Case
from .conftest import _make_request_case_list


def test_cases(api_request_factory: APIRequestFactory, cases: dict[str, Case]):
    # act
    response = _make_request_case_list(api_request_factory)

    # assert
    _assert_cases_list(response, expected_case_states={'NY', 'CT'})


def test_cases_filter_state(api_request_factory: APIRequestFactory, cases: dict[str, Case]):
    # act
    response = _make_request_case_list(api_request_factory, data=dict(
        state_code='NY'
    ))

    # assert
    _assert_cases_list(response, expected_case_states={'NY'})


def test_cases_filter_date_from(api_request_factory: APIRequestFactory, cases: dict[str, Case]):
    # act
    response = _make_request_case_list(api_request_factory, data=dict(
        date_from='2024-01-01'
    ))

    # assert
    _assert_cases_list(response, expected_case_states={'NY'})


def test_cases_filter_date_to(api_request_factory: APIRequestFactory, cases: dict[str, Case]):
    # act
    response = _make_request_case_list(api_request_factory, data=dict(
        date_to='2023-12-31'
    ))

    # assert
    _assert_cases_list(response, expected_case_states={'CT'})


def test_cases_filter_court(api_request_factory: APIRequestFactory, cases: dict[str, Case]):
    # act
    response = _make_request_case_list(api_request_factory, data=dict(
        court='supreme'
    ))

    # assert
    _assert_cases_list(response, expected_case_states={'NY'})


def test_cases_filter_case_type(api_request_factory: APIRequestFactory, cases: dict[str, Case]):
    # act
    response = _make_request_case_list(api_request_factory, data=dict(
        case_type='civil'
    ))

    # assert
    _assert_cases_list(response, expected_case_states={'NY'})


def test_cases_filter_caption(api_request_factory: APIRequestFactory, cases: dict[str, Case]):
    # act
    response = _make_request_case_list(api_request_factory, data=dict(
        caption='caption 1'
    ))

    # assert
    _assert_cases_list(response, expected_case_states={'NY'})



def _assert_cases_list(response, expected_case_states: set[str]):
    assert response.status_code == 200
    assert response.data['count'] == len(expected_case_states)
    assert {r['state_code'] for r in response.data['results']} == expected_case_states
