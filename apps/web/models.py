from django.db import models


class State(models.Model):
    code = models.CharField(max_length=5, unique=True)
    name = models.CharField(max_length=100, unique=True)
    website = models.URLField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.name


class CompanyInputName(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name_plural = "Company Inputs"

    def __str__(self):
        return self.name


class Case(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='cases')
    company = models.ForeignKey(CompanyInputName, on_delete=models.CASCADE, related_name='cases')
    court = models.CharField(max_length=255)
    case_id = models.CharField(max_length=255, unique=True)
    case_type = models.CharField(max_length=100)
    url = models.URLField(max_length=200)
    case_number = models.CharField(max_length=100, null=True)
    caption = models.TextField(null=True)
    received_date = models.DateField(null=True)
    file_date = models.DateField(null=True)
    return_date = models.DateField(null=True)
    additional_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.case_id} - {self.caption}"
