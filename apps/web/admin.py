from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import (State, Company, CompanyNameVariation, Case, CaseDetailsNY, CaseDetailsCT,
                     Document, DocumentDetailsNY, DocumentDetailsCT)


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'website']
    search_fields = ['name']
    ordering = ['name']


class CompanyNameVariationInline(admin.TabularInline):
    model = CompanyNameVariation
    extra = 1


class CaseInline(admin.TabularInline):
    model = Case
    can_delete = False
    extra = 0

    fields = ['case_number', 'caption']


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'name_variations_list'
    ]
    search_fields = ['name']
    ordering = ['name']
    inlines = [CaseInline, CompanyNameVariationInline]

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


class DocumentInline(admin.TabularInline):
    model = Document
    fields = ['name', 'url', 'is_downloaded']
    extra = 0


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = [
        'scraped_date', 'case_number', 'state_link', 'company_link', 'company_name_variation',
        'caption', 'court', 'case_type', 'gbruno_score'
    ]
    list_display_links = ['case_number', 'caption']
    search_fields = ['case_number', 'caption', 'company__name']
    # ordering = ['received_date']
    list_filter = ['state', 'case_type']
    list_select_related = ['state', 'company']  # Optimize foreign key lookups
    inlines = [DocumentInline]

    def company_link(self, obj):
        link = reverse("admin:web_company_change", args=[obj.company.id])
        return format_html('<a href="{}"><b>{}</b></a>', link, obj.company.name)
    company_link.short_description = 'Company'

    def state_link(self, obj):
        link = reverse("admin:web_state_change", args=[obj.company.id])
        return format_html('<a href="{}"><b>{}</b></a>', link, obj.state.code)
    state_link.short_description = 'State'

    def get_inlines(self, request, obj=None):
        inlines = list(super().get_inlines(request, obj))
        if obj:
            # Dynamically adjust inlines based on the state-specific details available
            if hasattr(obj, 'ny_details'):
                inlines = [CaseDetailsNyInline] + inlines
            if hasattr(obj, 'ct_details'):
                inlines = [CaseDetailsCTInline] + inlines
        return inlines


class DocumentDetailsNyInline(admin.StackedInline):
    model = DocumentDetailsNY
    can_delete = False


class DocumentDetailsCTInline(admin.StackedInline):
    model = DocumentDetailsCT
    can_delete = False


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['case', 'name', 'url']

    def get_inlines(self, request, obj=None):
        inlines = list(super().get_inlines(request, obj))
        if obj:
            # Dynamically adjust inlines based on the state-specific details available
            if hasattr(obj, 'ny_details'):
                inlines = [DocumentDetailsNyInline] + inlines
            if hasattr(obj, 'ct_details'):
                inlines = [DocumentDetailsCTInline] + inlines
        return inlines