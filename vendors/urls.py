from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VendorViewSet, AllVendorsView, VendorUpdateView, UnapprovedVendorsView, VendorApprovalView

# Create a router and register our VendorViewSet
router = DefaultRouter()
router.register(r'vendors', VendorViewSet, basename='vendor')

urlpatterns = [
    path('meta/', include(router.urls)),
    path('all-vendors/', AllVendorsView.as_view()),
    path('unapproved/', UnapprovedVendorsView.as_view(), name='unapproved-vendors'),
    path('<int:id>/update/', VendorUpdateView.as_view(), name='vendor-update'),
    path('<int:id>/approve/', VendorApprovalView.as_view(), name='vendor-approve'),
]
