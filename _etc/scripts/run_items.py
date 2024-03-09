from utils.django import django_setup_decorator
from datetime import date


@django_setup_decorator(environment='dev')
def run():
    from scraping_service.items import CaseItem, CaseItemCT, CaseItemNY
    from apps.web.models import State, Company, Case
    Case.objects.filter(case_id='TEST_VLAD').delete()
    item = CaseItemCT(
        state=State.objects.get(code='CT'),
        company=Company.objects.first(),
        company_name='company_name',

        case_id='TEST_VLAD',
        case_number='case_number',
        case_type='case_type',
        court='court',
        caption='caption',
        url='http://example.com',
        party_name='party_name',
        pty_no='pty_no',
        self_rep=True,
        prefix='prefix',
        file_date=date.today(),
        return_date=date.today(),
    )
    # # convert item to Case model
    # case = item.to_record()
    #
    # # save Case
    # case.save()
    #
    # # save CaseDetails
    # if hasattr(case, 'ct_details'):
    #     case.ct_details.save()
    # elif hasattr(case, 'ny_details'):
    #     case.ny_details.save()


@django_setup_decorator(environment='dev')
def run_directly():
    from apps.web.models import State, Company, Case, CaseDetailsCT
    Case.objects.filter(case_id='TEST_VLAD').delete()
    case = Case(
        state=State.objects.get(code='CT'),
        company=Company.objects.first(),
        company_name_variation='company_name',

        case_id='TEST_VLAD',
        case_number='case_number',
        case_type='case_type',
        court='court',
        caption='caption',
        url='http://example.com',
    )
    print(case)

    case_detail = CaseDetailsCT(
        case=case,
        party_name='party_name',
        pty_no='pty_no',
        self_rep=True,
        prefix='prefix',
        file_date=date.today(),
        return_date=date.today()
    )
    print(case_detail)
    case.save()
    case_detail.save()

    # # convert item to Case model
    # case = item.to_record()
    #
    # # save Case
    # case.save()
    #
    # # save CaseDetails
    # if hasattr(case, 'ct_details'):
    #     case.ct_details.save()
    # elif hasattr(case, 'ny_details'):
    #     case.ny_details.save()


if __name__ == '__main__':
    run_directly()
