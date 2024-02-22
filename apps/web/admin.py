from django.contrib import admin
from .models import State, CompanyInputName, Case


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'website']
    search_fields = ['name']
    ordering = ['name']


@admin.register(CompanyInputName)
class CompanyInputNameAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ['state', 'company', 'case_number', 'caption', 'court', 'case_type', 'received_date']
    list_display_links = ['case_number', 'caption']
    search_fields = ['case_number', 'caption']
    ordering = ['received_date']
    list_filter = ['state', 'company', 'case_type', 'court', 'received_date']
    list_select_related = ['state', 'company']  # Optimize foreign key lookups
