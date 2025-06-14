from django.urls import path
from .views import *

urlpatterns = [
    path('all-sales/', AllSalesView.as_view()),
    path('vendor-sales/', SalesByVendors.as_view()),
    path('customer-purchases/', PurchasesByCustomers.as_view()),
    path('buy-number/', BuyNumberView.as_view()),
]