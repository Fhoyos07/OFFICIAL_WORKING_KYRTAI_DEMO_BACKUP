from scraping_service.settings import INPUT_CSV_PATH, FILES_DIR
from django.db import transaction
from django.db.models import Count
from datetime import datetime
from tqdm import tqdm
import json

from utils.django import django_setup_decorator
from utils.file import load_csv


@django_setup_decorator(environment='dev')
def import_company_names():
    from apps.web.models import Company
    companies_to_insert: list[Company] = []
    for row in load_csv(INPUT_CSV_PATH):
        company = row['Competitor / Fictitious LLC Name'].strip().upper()
        companies_to_insert.append(Company(name=company))

    Company.objects.bulk_create(companies_to_insert)
    print(f'Inserted {len(companies_to_insert)} companies')


def get_companies_by_name():
    from apps.web.models import Company
    companies_by_name: dict[str, Company] = {}
    for company in Company.objects.all().prefetch_related('name_variations'):
        companies_by_name[company.name] = company
        for name_variation in company.name_variations.all():
            companies_by_name[name_variation.name] = company
    # print(f"companies_by_name: {json.dumps({
    #     k: v.name for k, v in companies_by_name.items()
    # }, indent=2, ensure_ascii=False)}")
    return companies_by_name


@django_setup_decorator(environment='dev')
@transaction.atomic()
def import_ny_cases():
    from apps.web.models import State, Company, Case, CaseDetailsNY
    state_code = 'NY'
    cases_path = FILES_DIR / state_code / 'cases.csv'
    state = State.objects.get(code=state_code)
    companies_by_name = get_companies_by_name()

    for row in tqdm(load_csv(cases_path)):
        company_name = row['Company']
        company = companies_by_name.get(company_name)
        if not company:
            print(f"Company or company variation not found for {repr(company_name)}. Skipping row.")
            continue

        # Proceed with case creation or retrieval
        case = Case.objects.create(
            state=state,
            company=company,
            company_name_variation=company_name,

            case_id=row['Case Id'],
            case_number=row['Case Number'],
            case_type=row['Case Type'],
            court=row['Court'],
            caption=row['Caption'],
            url=row['URL'],
        )

        # Only add CaseDetailsNY if the Case was newly created
        CaseDetailsNY.objects.create(
            case=case,
            received_date=datetime.strptime(row['Date'], '%Y-%m-%d').date(),
            efiling_status=row['eFiling Status'],
            case_status=row['Case Status'],
        )


@django_setup_decorator(environment='dev')
@transaction.atomic()
def import_ct_cases():
    from apps.web.models import State, Company, Case, CaseDetailsCT
    state_code = 'CT'
    cases_path = FILES_DIR / state_code / 'cases.csv'
    state = State.objects.get(code=state_code)
    companies_by_name = get_companies_by_name()

    for row in tqdm(load_csv(cases_path)):
        company_name = row['Company']
        company = companies_by_name.get(company_name)
        if not company:
            print(f"Company or company variation not found for {repr(company_name)}. Skipping row.")
            continue

        # Create the Case record
        case = Case.objects.create(
            state=state,
            company=company,
            company_name_variation=company_name,

            case_id=row['Case Id'],
            case_number=row['Case Number'],
            case_type=row['Case Type'],
            court=row['Court'],
            caption=row['Case Name'],
            url=row['URL'],
        )

        CaseDetailsCT.objects.create(
            case=case,
            party_name=row['Party Name'],
            pty_no=row['Pty No'],
            self_rep=True if row['Self-Rep'] and row['Self-Rep'].lower() == 'y' else False,
            prefix=row['Prefix'],
            file_date=row['File Date'] or None,
            return_date=row['Return Date'] or None,
        )


@django_setup_decorator(environment='dev')
@transaction.atomic()
def import_ny_documents():
    from apps.web.models import State, Case, Document, DocumentDetailsNY
    state_code = 'NY'
    cases_path = FILES_DIR / state_code / 'documents.csv'
    cases_by_number = {c.case_number: c for c in Case.objects.all().select_related('company')}

    documents_to_insert: list[Document] = []
    document_detail_by_id: dict[str, DocumentDetailsNY] = {}
    for row in tqdm(load_csv(cases_path)):
        document_id, case_number = row['Document ID'], row['Case Number']
        case = cases_by_number.get(case_number)
        if not case:
            print(f"Case number not found for {repr(case_number)}. Skipping row.")
            continue

        document = Document(
            company=case.company,
            case=case,
            name=row['Document Name'],
            document_id=document_id,
            url=row['Document URL'],
        )
        documents_to_insert.append(document)

        document_detail = DocumentDetailsNY(
            document=document,
            status_document_url=row['Status Document URL'],
            status_document_name=row['Status Document Name'],
        )
        document_detail_by_id[document_id] = document_detail

    documents = Document.objects.bulk_create(documents_to_insert)
    print(f'Inserted {len(documents)} documents')

    documents_by_id = {d.document_id: d for d in documents}
    for document_id, document_detail in document_detail_by_id.items():
        document_detail.document = documents_by_id[document_id]

    document_details = DocumentDetailsNY.objects.bulk_create(document_detail_by_id.values())
    print(f'Inserted {len(document_details)} details')


@django_setup_decorator(environment='dev')
@transaction.atomic()
def import_ct_documents():
    from apps.web.models import State, Case, Document, DocumentDetailsCT
    state_code = 'CT'
    cases_path = FILES_DIR / state_code / 'documents.csv'
    cases_by_number = {c.case_number: c for c in Case.objects.all().select_related('company')}

    documents_to_insert: list[Document] = []
    document_detail_by_id: dict[str, DocumentDetailsCT] = {}
    for row in tqdm(load_csv(cases_path)):
        document_id, case_number = row['Document ID'], row['Case Number']
        case = cases_by_number.get(case_number)
        if not case:
            print(f"Case number not found for {repr(case_number)}. Skipping row.")
            continue

        document = Document(
            company=case.company,
            case=case,
            name=row['Document Name'],
            document_id=document_id,
            url=row['Document URL'],
        )
        documents_to_insert.append(document)

        document_detail = DocumentDetailsCT(
            document=document,
            entry_no=row['Entry No'],
            file_date=row['File Date'],
            filed_by=row['Filed By'],
            arguable=row['Arguable'],
        )
        document_detail_by_id[document_id] = document_detail

    documents = Document.objects.bulk_create(documents_to_insert)
    print(f'Inserted {len(documents)} documents')

    documents_by_id = {d.document_id: d for d in documents}
    for document_id, document_detail in document_detail_by_id.items():
        document_detail.document = documents_by_id[document_id]

    document_details = DocumentDetailsCT.objects.bulk_create(document_detail_by_id.values())
    print(f'Inserted {len(document_details)} details')


@django_setup_decorator(environment='dev')
def find_duplicates():
    from apps.web.models import Company
    # Aggregate companies by name, counting the number of occurrences of each name
    company_counts = Company.objects.values('name').annotate(name_count=Count('id')).order_by().filter(name_count__gt=1)
    companies = Company.objects.filter(name__in=[r['name'] for r in company_counts]).prefetch_related('cases')
    # Display the list of duplicated company names
    for company in companies:
        print(f"Company Name: {company.name}, cases: {company.cases.count()}")
        if company.cases.count() == 0:
            company.delete()


if __name__ == '__main__':
    import_ct_documents()
    # import_ny_cases()
    # import_ct_cases()
    # find_duplicates()
