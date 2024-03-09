from datetime import datetime, date
from dataclasses import dataclass, field


@dataclass
class CaseItem:
    case_id: str = field(default=None)
    company: str = field(default=None)
    case_number: str = field(default=None)
    case_type: str = field(default=None)
    court: str = field(default=None)
    url: str = field(default=None)

    state_specific_info: 'CaseItemForState' = field(default=None)


class CaseItemForState:
    state: str = field(default=None)


@dataclass
class CaseItemNy(CaseItemForState):
    received_date: date = field(default=None)
    efiling_status: str = field(default=None)
    case_status: str = field(default=None)
    caption: str = field(default=None)

    state: str = field(default='NY')  # Override default value


@dataclass
class CaseItemCT(CaseItemForState):
    case_name: str = field(default=None)
    party_name: str = field(default=None)
    pty_no: str = field(default=None)
    self_rep: str = field(default=None)
    prefix: str = field(default=None)
    file_date: date = field(default=None)
    return_date: date = field(default=None)

    state: str = field(default='CT')  # Override default value


# - - - - - - -
# document item
@dataclass
class DocumentItem:
    url: str = field(default=None)
    company: str = field(default=None)
    case: str = field(default=None)
    name: str = field(default=None)
    document_id: str = field(default=None)
    state_specific_info: 'DocumentItemForState' = field(default=None)


@dataclass
class DocumentItemForState:
    state: str = field(default=None)


@dataclass
class DocumentItemNy(DocumentItemForState):
    status_document_url: str = field(default=None)
    status_document_name: str = field(default=None)

    state: str = field(default='NY')  # Override default value


@dataclass
class DocumentItemCT(DocumentItemForState):
    entry_no: str = field(default=None)
    file_date: str = field(default=None)
    filed_by: str = field(default=None)
    arguable: str = field(default=None)

    state: str = field(default='CT')  # Override default value
