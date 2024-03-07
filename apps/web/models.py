from django.db import models


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
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ['company', 'name']

    def __str__(self):
        return self.name


from django.core.validators import MaxValueValidator, MinValueValidator
class Case(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='cases')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='cases')
    company_name = models.CharField(max_length=255, null=True, blank=True)

    case_id = models.CharField(max_length=255, null=True, blank=True)
    case_number = models.CharField(max_length=255, null=True, blank=True)
    case_type = models.CharField(max_length=255, null=True, blank=True)
    court = models.CharField(max_length=255, null=True, blank=True)
    caption = models.CharField(max_length=2000, null=True, blank=True)
    url = models.URLField(null=True, blank=True)

    gbruno_score = models.IntegerField(null=True, blank=True, validators=[
        MinValueValidator(0), MaxValueValidator(100)
    ])


class CaseDetailsNY(models.Model):
    case = models.OneToOneField(Case, on_delete=models.CASCADE, related_name='ny_details')

    received_date = models.DateField(null=True, blank=True)
    efiling_status = models.CharField(max_length=255, null=True, blank=True)
    case_status = models.CharField(max_length=255, null=True, blank=True)


class CaseDetailsCT(models.Model):
    case = models.OneToOneField(Case, on_delete=models.CASCADE, related_name='ct_details')

    party_name = models.CharField(max_length=255, null=True, blank=True)
    pty_no = models.CharField(max_length=255, null=True, blank=True)
    self_rep = models.BooleanField(default=False)
    prefix = models.CharField(max_length=255, null=True, blank=True)
    file_date = models.DateField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)
