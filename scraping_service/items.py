from datetime import datetime, date
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from apps.web.models import (State, Company, Case, CaseDetailsNY, CaseDetailsCT,
                             Document, DocumentDetailsNY, DocumentDetailsCT)


@dataclass
class CaseItem(ABC):
    state: State = field(default=None)
    company: Company = field(default=None)
    company_name_variation: str = field(default=None)

    docket_id: str = field(default=None)
    case_number: str = field(default=None)
    case_type: str = field(default=None)
    court: str = field(default=None)
    caption: str = field(default=None)
    status: str = field(default=None)
    url: str = field(default=None)

    filed_date: date = field(default=None)
    received_date: date = field(default=None)

    case: Case = field(default=None)

    @abstractmethod
    def to_record(self) -> Case:
        case = self.case if self.case else Case()
        case.state = self.state
        case.company = self.company
        case.company_name_variation = self.company_name_variation

        case.docket_id = self.docket_id
        case.case_number = self.case_number
        case.case_type = self.case_type
        case.court = self.court
        case.caption = self.caption
        case.status = self.status
        case.url = self.url

        case.filed_date = self.filed_date
        case.received_date = self.received_date
        return case


@dataclass
class CaseItemNY(CaseItem):
    efiling_status: str = field(default=None)

    def to_record(self) -> Case:
        case = super().to_record()

        if not hasattr(case, 'ny_details'):
            case.ny_details = CaseDetailsNY()

        case.ny_details.efiling_status = self.efiling_status
        return case


@dataclass
class CaseItemCT(CaseItem):
    party_name: str = field(default=None)
    pty_no: str = field(default=None)
    self_rep: bool = field(default=None)
    prefix: str = field(default=None)
    return_date: date = field(default=None)

    def to_record(self) -> Case:
        case = super().to_record()

        if not hasattr(case, 'ct_details'):
            case.ct_details = CaseDetailsCT()

        case.ct_details.party_name = self.party_name
        case.ct_details.pty_no = self.pty_no
        case.ct_details.self_rep = self.self_rep
        case.ct_details.prefix = self.prefix
        case.ct_details.return_date = self.return_date
        return case


# - - - - - - -
# document item
@dataclass
class DocumentItem:
    case: Case = field(default=None)
    url: str = field(default=None)
    name: str = field(default=None)
    document_id: str = field(default=None)

    def to_record(self) -> Document:
        return Document(
            case=self.case,
            url=self.url,
            name=self.name,
            document_id=self.document_id,
        )


@dataclass
class DocumentItemNY(DocumentItem):
    status_document_url: str = field(default=None)
    status_document_name: str = field(default=None)


@dataclass
class DocumentItemCT(DocumentItem):
    entry_no: str = field(default=None)
    file_date: str = field(default=None)
    filed_by: str = field(default=None)
    arguable: str = field(default=None)
