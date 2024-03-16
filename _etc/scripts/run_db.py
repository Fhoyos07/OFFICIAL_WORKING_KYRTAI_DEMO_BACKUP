from datetime import datetime, timezone

from utils.django import django_setup, django_setup_decorator
from django.db import transaction
import re


@django_setup_decorator(environment='dev')
def deduplicate_companies():
    from apps.web.models import Case
    cases = Case.objects.all().select_related('ny_details', 'ct_details')
    cases_to_update = []
    for case in cases:
        if hasattr(case, 'ny_details'):
            case.status = case.ny_details.case_status
            case.received_date = case.ny_details.received_date
        elif hasattr(case, 'ct_details'):
            case.filed_date = case.ct_details.filed_date
        cases_to_update.append(case)
    Case.objects.bulk_update(cases_to_update, fields=[
        'status', 'received_date', 'filed_date'
    ])


@django_setup_decorator(environment='dev')
def update_scraped_date():
    from apps.web.models import Case
    Case.objects.filter(
        state__code='NY', scraped_date__isnull=True
    ).update(
        scraped_date=datetime(2024, 2, 1, tzinfo=timezone.utc)
    )


if __name__ == '__main__':
    update_scraped_date()
