from django.db import models
from datetime import datetime, date
from django.utils import timezone
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from apps.web.models import (State, Company, Case, CaseDetailsNY, CaseDetailsCT,
                             Document, DocumentDetailsNY, DocumentDetailsCT)


@dataclass
class DbItem:
    record: Case | Document


@dataclass
class DocumentBodyItem:
    record: Document
    body: bytes
    relative_path: str = field(default=None)
