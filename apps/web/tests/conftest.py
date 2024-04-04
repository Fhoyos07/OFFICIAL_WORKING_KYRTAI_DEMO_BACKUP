import pytest
from rest_framework.test import APIRequestFactory
from rest_framework_api_key.models import APIKey
from apps.web.models import State, Company, Case


@pytest.fixture
def state_ny(db) -> State:
    return State.objects.create(code='NY', name='New York')


@pytest.fixture
def state_ct(db) -> State:
    return State.objects.create(code='CT', name='Connecticut')


@pytest.fixture
def company_first(db) -> Company:
    return Company.objects.create(name='First')


@pytest.fixture
def company_second(db) -> Company:
    return Company.objects.create(name='Second')


@pytest.fixture
def companies(company_first: Company, company_second: Company) -> dict[str, Company]:
    return dict(
        first=company_first,
        second=company_second
    )


@pytest.fixture
def case_ny(db, state_ny: State, company_first: Company) -> Case:
    return Case.objects.create(
        state=state_ny,
        company=company_first,
        case_date='2024-01-01',
        court='Supreme Court',
        case_type='Civil',
        caption='Caption 1'
    )


@pytest.fixture
def case_ct(db, state_ct: State, company_second: Company) -> Case:
    return Case.objects.create(
        state=state_ct,
        company=company_second,
        case_date='2023-01-01',
        court='Civil Court',
        case_type='Criminal',
        caption='Caption 2'
    )


@pytest.fixture
def cases(case_ny: Case, case_ct: Case) -> dict[str, Case]:
    return dict(
        ny=case_ny,
        ct=case_ct
    )


@pytest.fixture
def api_key(db) -> str:
    _, key = APIKey.objects.create_key(name="test")
    return key


@pytest.fixture
def api_request_factory(api_key: str) -> APIRequestFactory:
    return APIRequestFactory(headers={'X-API-KEY': api_key})


def _make_request_case_list(api_request_factory: APIRequestFactory, data: dict = None):
    from apps.web.views import CaseViewSet
    view = CaseViewSet.as_view({'get': 'list'})
    request = api_request_factory.get("/cases/", data=data)
    return view(request)


def _make_request_companies_list(api_request_factory: APIRequestFactory, data: dict = None):
    from apps.web.views import CompanyViewSet
    view = CompanyViewSet.as_view({'get': 'list'})
    request = api_request_factory.get("/companies/", data=data)
    return view(request)
