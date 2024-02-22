from scraping_service.settings import INPUT_CSV_PATH
from scraping_service.utils.django import django_setup, django_setup_decorator
from scraping_service.utils.file import load_csv


@django_setup_decorator(environment='dev')
def import_company_names():
    from apps.web.models import CompanyInputName
    companies_to_insert: list[CompanyInputName] = []
    for row in load_csv(INPUT_CSV_PATH):
        company = row['Competitor / Fictitious LLC Name'].strip().upper()
        companies_to_insert.append(CompanyInputName(name=company))

    CompanyInputName.objects.bulk_create(companies_to_insert)
    print(f'Inserted {len(companies_to_insert)} companies')


if __name__ == '__main__':
    import_company_names()
