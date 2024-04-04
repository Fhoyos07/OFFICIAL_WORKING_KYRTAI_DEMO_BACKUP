from rest_framework import permissions, viewsets
import django_filters

from .serializers import CompanySerializer, CaseSerializer
from .models import Company, Case


class CompanyFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Company
        fields = ['name']


class CompanyViewSet(viewsets.ReadOnlyModelViewSet):  # Use ReadOnlyModelViewSet for list and retrieve actions
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    filterset_class = CompanyFilter


class CaseFilter(django_filters.FilterSet):
    state_code = django_filters.CharFilter(field_name='state__code', lookup_expr='iexact')
    date_from = django_filters.DateFilter(field_name='case_date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='case_date', lookup_expr='lte')
    court = django_filters.CharFilter(field_name='court', lookup_expr='icontains')
    case_type = django_filters.CharFilter(field_name='case_type', lookup_expr='iexact')
    caption = django_filters.CharFilter(field_name='caption', lookup_expr='icontains')

    class Meta:
        model = Case
        fields = []


class CaseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer
    filterset_class = CaseFilter
