from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator


class State(models.Model):
    code = models.CharField(max_length=5, unique=True)
    name = models.CharField(max_length=100, unique=True)
    website = models.URLField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.name


class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.name


class CompanyNameVariation(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='name_variations')
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        unique_together = ['company', 'name']
        ordering = ['name']

    def __str__(self):
        return self.name


# CASE models
class Case(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='cases')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='cases')
    company_name_variation = models.CharField(max_length=255, null=True, blank=True)

    docket_id = models.CharField(max_length=255, null=True, blank=True)
    case_number = models.CharField(max_length=255, null=True, blank=True)
    case_type = models.CharField(max_length=255, null=True, blank=True)
    court = models.CharField(max_length=255, null=True, blank=True)
    caption = models.CharField(max_length=2000, null=True, blank=True)
    url = models.URLField(null=True, blank=True)

    status = models.CharField(max_length=100, null=True, blank=True)

    filed_date = models.DateField(null=True, blank=True)
    received_date = models.DateField(null=True, blank=True)

    found_date = models.DateTimeField(null=True, blank=True)

    is_scraped = models.BooleanField(default=False)
    scraped_date = models.DateTimeField(null=True, blank=True)

    gbruno_score = models.IntegerField(null=True, blank=True, validators=[
        MinValueValidator(0), MaxValueValidator(100)
    ])
    case_date = models.DateField()

    def __str__(self):
        return self.case_number

    class Meta:
        unique_together = ('state', 'docket_id')


class CaseDetailsNY(models.Model):
    case = models.OneToOneField(Case, on_delete=models.CASCADE, related_name='ny_details')

    efiling_status = models.CharField(max_length=255, null=True, blank=True)
    # status_document_url = models.URLField(max_length=255, blank=True, null=True)
    # status_document_name = models.CharField(max_length=255, blank=True, null=True)


class CaseDetailsCT(models.Model):
    case = models.OneToOneField(Case, on_delete=models.CASCADE, related_name='ct_details')

    party_name = models.CharField(max_length=255, null=True, blank=True)
    pty_no = models.CharField(max_length=255, null=True, blank=True)
    self_rep = models.BooleanField(default=False)
    prefix = models.CharField(max_length=255, null=True, blank=True)
    # file_date = models.DateField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f'{self.case.case_number} Details'


class CaseDetailsMN(models.Model):
    case = models.OneToOneField(Case, on_delete=models.CASCADE, related_name='mn_details')


# DOCUMENT Models
class Document(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='documents')
    name = models.CharField(max_length=255, blank=True, null=True)
    document_id = models.CharField(max_length=255, blank=True, null=True)
    url = models.URLField(max_length=255, blank=True, null=True)

    is_downloaded = models.BooleanField(default=False)
    download_date = models.DateTimeField(null=True, blank=True)

    relative_path = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        unique_together = ('case', 'document_id')

    def __str__(self):
        return self.name

    @property
    def s3_url(self) -> str:
        if self.relative_path:
            return f'https://s3.us-east-2.amazonaws.com/{settings.AWS_S3_BUCKET_NAME}/{self.relative_path}'


class DocumentDetailsNY(models.Model):
    document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name='ny_details')
    status_document_url = models.URLField(max_length=255, blank=True, null=True)
    status_document_name = models.CharField(max_length=255, blank=True, null=True)


class DocumentDetailsCT(models.Model):
    document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name='ct_details')
    entry_no = models.CharField(max_length=255, blank=True, null=True)
    filed_date = models.DateField(null=True, blank=True)
    filed_by = models.CharField(max_length=255, blank=True, null=True)
    arguable = models.CharField(max_length=255, blank=True, null=True)


class DocumentDetailsMN(models.Model):
    document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name='mn_details')
