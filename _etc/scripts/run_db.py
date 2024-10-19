from datetime import datetime, timezone

from utils.django import django_setup, django_setup_decorator
from django.db import transaction
from tqdm import tqdm
from utils.types.array import chunked_list
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


@django_setup_decorator(environment='dev')
def cleanup_company_variations():
    from apps.web.models import Company, CompanyNameVariation
    companies = list(Company.objects.prefetch_related('name_variations').all())
    companies_to_update: list[Company] = []
    variation_ids_to_delete: list[int] = []
    for company in companies:
        company_variations = list(company.name_variations.all())
        for variation in company_variations:
            if variation.name == f'{company.name}, LLC' and len(company_variations) == 1:
                company.name = f'{company.name} LLC'
                companies_to_update.append(company)
                variation_ids_to_delete.append(variation.id)

    with transaction.atomic():
        CompanyNameVariation.objects.filter(id__in=variation_ids_to_delete).delete()
        print(f'Deleted {len(variation_ids_to_delete)} variations')

        Company.objects.bulk_update(companies_to_update, fields=['name'])
        print(f'Updated {len(companies_to_update)} companies')


@django_setup_decorator(environment='dev')
def update_dates():
    from apps.web.models import Case
    cases = Case.objects.prefetch_related('state').all()
    for case in cases:
        if case.state.code == 'CT':
            case.case_date = case.filed_date
        elif case.state.code == 'NY':
            case.case_date = case.received_date

    progress_bar = tqdm(total=len(cases))
    with transaction.atomic():
        for chunk in chunked_list(cases, chunk_size=100):
            Case.objects.bulk_update(chunk, fields=['case_date'])
            progress_bar.update(len(chunk))


if __name__ == '__main__':
    update_dates()
