from .models import Company, Case
from rest_framework import serializers


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name']


class CaseSerializer(serializers.ModelSerializer):
    state_code = serializers.CharField(source='state.code', read_only=True)

    class Meta:
        model = Case
        fields = ['id', 'case_number', 'state_code', 'caption', 'case_date', 'court', 'case_type']
