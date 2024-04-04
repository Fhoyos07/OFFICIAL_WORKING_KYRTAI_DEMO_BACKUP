import pytest
from django.test import RequestFactory
from django_filters import CharFilter, DateFilter
from apps.web.views import CaseFilter
from apps.web.models import Case, State
pytestmark = [pytest.mark.django_db]


@pytest.fixture
def state():
    # Assuming State model has a field 'code'
    return State.objects.create(code='NY')

@pytest.fixture
def case(state):
    return Case.objects.create(
        state=state,
        case_date='2022-01-01',
        court='Supreme Court',
        case_type='Civil',
        caption='Test Case'
    )

@pytest.fixture
def case_filter(case):
    factory = RequestFactory()
    request = factory.get('/', {'stateCode': 'NY', 'dateFrom': '2022-01-01', 'dateTo': '2022-12-31', 'court': 'Supreme', 'caseType': 'Civil', 'caption': 'Test'})
    return CaseFilter(request.GET, queryset=Case.objects.all())


def test_case_filter_state_code(case_filter):
    assert isinstance(case_filter.filters['stateCode'], CharFilter)
    assert case_filter.qs.count() == 1

def test_case_filter_date_from(case_filter):
    assert isinstance(case_filter.filters['dateFrom'], DateFilter)
    assert case_filter.qs.count() == 1

def test_case_filter_date_to(case_filter):
    assert isinstance(case_filter.filters['dateTo'], DateFilter)
    assert case_filter.qs.count() == 1

def test_case_filter_court(case_filter):
    assert isinstance(case_filter.filters['court'], CharFilter)
    assert case_filter.qs.count() == 1

def test_case_filter_case_type(case_filter):
    assert isinstance(case_filter.filters['caseType'], CharFilter)
    assert case_filter.qs.count() == 1

def test_case_filter_caption(case_filter):
    assert isinstance(case_filter.filters['caption'], CharFilter)
    assert case_filter.qs.count() == 1