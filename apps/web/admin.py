from django.contrib import admin
from django.db.models import Prefetch, Count, F
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from .models import (State, Company, CompanyNameVariation, Case, CaseDetailsNY, CaseDetailsCT, CaseDetailsMN,
                     Document, DocumentDetailsNY, DocumentDetailsCT, DocumentDetailsMN)


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
    extra = 0

    can_delete = False
    fields = readonly_fields = ['case_number', 'caption']


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'name_variations_list'
    ]
    search_fields = ['name']
    inlines = [
        # CaseInline,
        CompanyNameVariationInline
    ]

    def get_queryset(self, request):
        queryset = super().get_queryset(request).prefetch_related('name_variations')
        return queryset

    def name_variations_list(self, obj: Company):
        variations = [variation.name for variation in obj.name_variations.all()]
        variations_str = '<br/>'.join(variations)
        if len(variations_str) > 3000:
            variations_str = f'{variations_str[:3000]}...'
        return format_html(variations_str)

    name_variations_list.short_description = 'Name Variations'


@admin.register(CompanyNameVariation)
class CompanyNameVariationAdmin(admin.ModelAdmin):
    list_display = ['name', 'company']
    ordering = ['name']
    search_fields = ['name']


# CASE INLINES
class CaseDetailsNyInline(admin.StackedInline):
    model = CaseDetailsNY
    can_delete = False


class CaseDetailsCtInline(admin.StackedInline):
    model = CaseDetailsCT
    can_delete = False


class CaseDetailsMnInline(admin.StackedInline):
    model = CaseDetailsMN
    can_delete = False


class DocumentInline(admin.TabularInline):
    model = Document
    fields = readonly_fields = ['name', 's3_url', 'original_url']
    extra = 0

    def s3_url(self, instance: Document):
        if instance.s3_url:
            return mark_safe(f'<a href="{instance.s3_url}">{instance.s3_url}</a>')
        return "-"
    s3_url.short_description = "S3 URL"

    def original_url(self, instance: Document):
        if instance.url:
            return mark_safe(f'<a href="{instance.url}">{instance.url}</a>')
        return "-"
    original_url.short_description = "URL"


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = [
        'found_date', 'case_number', 'state_link', 'company_link', 'company_name_variation', 'documents_count',
        'caption', 'case_type', 'case_date', 'gbruno_score'
    ]
    list_display_links = ['case_number', 'caption']
    search_fields = ['case_number', 'caption', 'company__name', 'docket_id']
    list_filter = ['state', 'case_type']
    list_select_related = ['state', 'company']  # Optimize foreign key lookups

    readonly_fields = ['url']

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
                inlines = [CaseDetailsCtInline] + inlines
            if hasattr(obj, 'mn_details'):
                inlines = [CaseDetailsMnInline] + inlines
        return inlines

    def documents_count(self, obj):
        return format_html(f'{obj.documents_count}')
    documents_count.short_description = 'Documents'

    def get_queryset(self, request):
        """Performance optimization"""
        queryset = super().get_queryset(request)
        queryset = queryset.select_related(
            'state',
            'company'
        ).prefetch_related(
            Prefetch('documents'),
        ).annotate(
            documents_count=Count('documents')
        )
        return queryset


class DocumentDetailsNyInline(admin.StackedInline):
    model = DocumentDetailsNY
    can_delete = False


class DocumentDetailsCtInline(admin.StackedInline):
    model = DocumentDetailsCT
    can_delete = False


class DocumentDetailsMnInline(admin.StackedInline):
    model = DocumentDetailsMN
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
                inlines = [DocumentDetailsCtInline] + inlines
            if hasattr(obj, 'mn_details'):
                inlines = [DocumentDetailsMnInline] + inlines
        return inlines
