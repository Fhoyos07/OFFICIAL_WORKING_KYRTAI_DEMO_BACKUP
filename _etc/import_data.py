from scraping_service.settings import INPUT_CSV_PATH, FILES_DIR
from utils.django import django_setup_decorator
from utils.file import load_csv
from django.db import transaction
from datetime import datetime
from django.db.models import Count
from tqdm import tqdm


@django_setup_decorator(environment='dev')
def import_company_names():
    from apps.web.models import CompanyInputName
    companies_to_insert: list[CompanyInputName] = []
    for row in load_csv(INPUT_CSV_PATH):
        company = row['Competitor / Fictitious LLC Name'].strip().upper()
        companies_to_insert.append(CompanyInputName(name=company))

    CompanyInputName.objects.bulk_create(companies_to_insert)
    print(f'Inserted {len(companies_to_insert)} companies')


@django_setup_decorator(environment='dev')
@transaction.atomic()
def import_ny_cases():
    from apps.web.models import State, CompanyInputName, Case
    ny_cases_path = FILES_DIR / 'NY' /  'cases.csv'
    for row in load_csv(ny_cases_path):
        state = State.objects.get(code='NY')
        company, _ = CompanyInputName.objects.get_or_create(name=row['Company'])

        # Create additional data dictionary
        additional_data = {
            'eFiling Status': row['eFiling Status'],
            'Case Status': row['Case Status']
        }

        # Create Case object
        case = Case.objects.create(
            state=state,
            company=company,
            court=row['Court'],
            case_id=row['Case Id'],
            case_type=row['Case Type'],
            url=row.get('URL'),  # URL is optional
            case_number=row['Case Number'],
            caption=row['Caption'],
            received_date=datetime.strptime(row['Date'], '%Y-%m-%d').date(),
            file_date=None,  # Assuming file_date should be today's date
            additional_data=additional_data,
        )

        print(f"Case created: {case}")

@django_setup_decorator(environment='dev')
@transaction.atomic()
def import_ct_cases():
    from apps.web.models import State, CompanyInputName, Case
    state = State.objects.get(code='CT')

    ct_cases_path = FILES_DIR / 'CT' /  'cases.csv'
    cases_to_create: list[Case] = []

    company_by_name = {}
    for row in tqdm(load_csv(ct_cases_path)):
        if row['Company'] not in company_by_name:
            company, _ = CompanyInputName.objects.get_or_create(name=row['Company'])
            company_by_name[row['Company']] = company

    for row in tqdm(load_csv(ct_cases_path)):
        company = company_by_name[row['Company']]

        # Prepare additional_data by excluding fields that are directly mapped
        direct_fields = {'Case Id', 'Company', 'Case Number', 'Case Name', 'Court', 'Case Type', 'URL', 'File Date', 'Return Date'}
        additional_data = {key: value for key, value in row.items() if key not in direct_fields}

        # Create the Case record
        cases_to_create.append(Case(
            state=state,
            company=company,
            court=row['Court'],
            case_id=row['Case Id'],
            case_number=row['Case Number'],
            caption=row['Case Name'],
            case_type=row['Case Type'],
            url=row['URL'],
            file_date=row.get('File Date'),
            return_date=row.get('Return Date'),
            additional_data=additional_data  # Store remaining data in additional_data JSON field
        ))
    Case.objects.bulk_create(cases_to_create)


@django_setup_decorator(environment='dev')
def find_duplicates():
    from apps.web.models import CompanyInputName
    # Aggregate companies by name, counting the number of occurrences of each name
    company_counts = CompanyInputName.objects.values('name').annotate(name_count=Count('id')).order_by().filter(name_count__gt=1)
    companies = CompanyInputName.objects.filter(name__in=[r['name'] for r in company_counts]).prefetch_related('cases')
    # Display the list of duplicated company names
    for company in companies:
        print(f"Company Name: {company.name}, cases: {company.cases.count()}")
        if company.cases.count() == 0:
            company.delete()


if __name__ == '__main__':
    # import_ct_cases()
    find_duplicates()
