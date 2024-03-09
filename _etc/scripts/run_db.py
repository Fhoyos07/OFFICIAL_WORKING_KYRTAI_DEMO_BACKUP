from utils.django import django_setup, django_setup_decorator
from django.db import transaction
import re


@django_setup_decorator(environment='dev')
def deduplicate_companies():
    from apps.web.models import Company, CompanyNameVariation
    main_company = Company.objects.get(name='J.G. WENTWORTH')
    companies = Company.objects.filter(name__contains='AKA JG').exclude(id=main_company.id).prefetch_related('name_variations')

    for company in companies:
        if company.name_variations.count() > 0:
            print(f'{company.name} contains {company.name_variations.count()} variations! Skipping!')
            continue
        CompanyNameVariation.objects.create(company=main_company, name=company.name)
        company.delete()
        print(f'Removed {company.name}')


if __name__ == '__main__':
    deduplicate_companies()
