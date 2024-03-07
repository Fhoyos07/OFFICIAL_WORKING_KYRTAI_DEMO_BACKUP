from django.contrib import admin
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import State, Company, CompanyNameVariation, Case, CaseDetailsNY, CaseDetailsCT


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'website']
    search_fields = ['name']
    ordering = ['name']


class CompanyNameVariationInline(admin.TabularInline):
    model = CompanyNameVariation
    extra = 1


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'name',
        'name_variations_list'
    ]
    search_fields = ['name']
    ordering = ['name']
    inlines = [CompanyNameVariationInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request).prefetch_related('name_variations')
        return queryset

    def name_variations_list(self, obj):
        variations = [variation.name for variation in obj.name_variations.all()]
        variations_str = ' | '.join(variations)
        if len(variations_str) > 2000:
            return format_html('{}...', variations_str[:2000])
        return variations_str
    name_variations_list.short_description = 'Name Variations'


class CaseDetailsNyInline(admin.StackedInline):
    model = CaseDetailsNY
    can_delete = False


class CaseDetailsCTInline(admin.StackedInline):
    model = CaseDetailsCT
    can_delete = False


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ['state', 'case_number', 'company_link', 'company_name', 'caption', 'court', 'case_type']

    def company_link(self, obj):
        link = reverse("admin:web_company_change", args=[obj.company.id])
        return format_html('<a href="{}"><b>{}</b></a>', link, obj.company.name)
    company_link.short_description = 'Company'  # Sets the column name

    inlines = [CaseDetailsNyInline, CaseDetailsCTInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related('state')
        return queryset

    def get_inlines(self, request, obj=None):
        inlines = super().get_inlines(request, obj)
        if obj:
            # Dynamically adjust inlines based on the state-specific details available
            if not hasattr(obj, 'ny_details'):
                inlines.remove(CaseDetailsNyInline)
            if not hasattr(obj, 'ct_details'):
                inlines.remove(CaseDetailsCTInline)
        return inlines

    list_display_links = ['case_number']
    search_fields = ['case_number', 'caption']
    # ordering = ['received_date']
    list_filter = ['state', 'case_type']
    # list_select_related = ['state', 'company']  # Optimize foreign key lookups
