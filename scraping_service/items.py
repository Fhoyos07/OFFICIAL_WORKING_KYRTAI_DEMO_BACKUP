from datetime import datetime, date
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from apps.web.models import (State, Company, Case, CaseDetailsNY, CaseDetailsCT,
                             Document, DocumentDetailsNY, DocumentDetailsCT)


@dataclass
class CaseItem(ABC):
    state: State = field(default=None)
    company: Company = field(default=None)
    company_name: str = field(default=None)

    case_id: str = field(default=None)
    case_number: str = field(default=None)
    case_type: str = field(default=None)
    court: str = field(default=None)
    caption: str = field(default=None)
    url: str = field(default=None)

    @abstractmethod
    def to_record(self) -> Case:
        return Case(
            state=self.state,
            company=self.company,
            company_name_variation=self.company_name,

            case_id=self.case_id,
            case_number=self.case_number,
            case_type=self.case_type,
            court=self.court,
            caption=self.caption,
            url=self.url
        )


@dataclass
class CaseItemNY(CaseItem):
    state: State = field(default=None)
    received_date: date = field(default=None)
    efiling_status: str = field(default=None)
    case_status: str = field(default=None)

    def to_record(self) -> Case:
        case = super().to_record()
        case.ny_details = CaseDetailsNY(
            received_date=self.received_date,
            efiling_status=self.efiling_status,
            case_status=self.case_status
        )
        return case


@dataclass
class CaseItemCT(CaseItem):
    party_name: str = field(default=None)
    pty_no: str = field(default=None)
    self_rep: bool = field(default=None)
    prefix: str = field(default=None)
    file_date: date = field(default=None)
    return_date: date = field(default=None)

    def to_record(self) -> Case:
        case = super().to_record()
        case.ct_details = CaseDetailsCT(
            party_name=self.party_name,
            pty_no=self.pty_no,
            self_rep=self.self_rep,
            prefix=self.prefix,
            file_date=self.file_date,
            return_date=self.return_date,
        )
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
            company=self.company,
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
