import pytest
from rest_framework.test import APIRequestFactory
from rest_framework_api_key.models import APIKey
from apps.web.models import Case, State, Company

pytestmark = [pytest.mark.django_db]


@pytest.fixture
def state_ny():
    return State.objects.create(code='NY', name='New York')


@pytest.fixture
def state_ct():
    return State.objects.create(code='CT', name='Connecticut')


@pytest.fixture
def company():
    return Company.objects.create(name='Company')


@pytest.fixture
def case_ny(state_ny, company):
    return Case.objects.create(
        state=state_ny,
        company=company,
        case_date='2024-01-01',
        court='Supreme Court',
        case_type='Civil',
        caption='Caption 1'
    )


@pytest.fixture
def case_ct(state_ct, company):
    return Case.objects.create(
        state=state_ct,
        company=company,
        case_date='2023-01-01',
        court='Civil Court',
        case_type='Criminal',
        caption='Caption 2'
    )


@pytest.fixture
def cases(case_ny, case_ct) -> dict[str, Case]:
    return dict(
        ny=case_ny,
        ct=case_ct
    )


@pytest.fixture
def api_key():
    _, key = APIKey.objects.create_key(name="test")
    return key


@pytest.fixture
def api_request_factory(api_key):
    return APIRequestFactory(headers={'X-API-KEY': api_key})