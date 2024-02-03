from pathlib import Path

from .spider_ny import KyrtNySearchSpider, KyrtNyCaseSpider, KyrtNyDocumentSpider
from ..settings import FILES_DIR


# Step 1 - search each company
class KyrtNyProceedingSearchSpider(KyrtNySearchSpider):
    name = 'kyrt_ny_proceeding_search'

    @property
    def state_code(self) -> str: return 'NY_proceedings'

    @property
    def input_csv_path(self) -> Path: return FILES_DIR / 'input_ny_proceedings.csv'

    @property
    def default_form_data(self):
        case_type_id = 'aEZuL9pb1E7fxwFgLLKgbw=='  # Special Proceeding - CPLR Article 78 - DHCR
        return {
            "recaptcha-is-invisible": "true",
            "rbnameType": "partyName",
            "txtPartyFirstName": "",
            "txtPartyMiddleName": "",
            "txtPartyLastName": "",
            "txtCounty": "-1",
            "txtCaseType": case_type_id,
            "txtFilingDateFrom": "",
            "txtFilingDateTo": "",
            "btnSubmit": "Search",
        }


class KyrtNyProceedingCaseSpider(KyrtNyCaseSpider):
    name = 'kyrt_ny_proceeding_cases'

    @property
    def state_code(self) -> str: return 'NY_proceedings'


class KyrtNyDocumentProceedingSpider(KyrtNyDocumentSpider):
    name = 'kyrt_ny_proceeding_documents'

    @property
    def state_code(self) -> str: return 'NY_proceedings'