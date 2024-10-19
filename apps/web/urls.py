from rest_framework import routers
from .views import CompanyViewSet, CaseViewSet

router = routers.DefaultRouter()
router.register(r'companies', CompanyViewSet)
router.register(r'cases', CaseViewSet)
