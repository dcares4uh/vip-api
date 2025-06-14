from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import permissions, status
from .serializers import SalesSerializer
from .models import *

class AllSalesView(APIView):
    permission_classes = [permissions.IsAdminUser]
    query_set = Sales.objects.all()
    serializer_class = SalesSerializer

class SalesByVendors(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SalesSerializer


    def get(self, request):
        try: 
            vendor = request.user.vendor_profile
        except Vendor.DoesNotExist:
            return Response({"error": "User is not associated with any vendor profile."}, status=403)
        
        sales = Sales.objects.filter(vendor=vendor)
        serializer = self.serializer_class(sales, many=True)

        return Response(serializer.data, status=200)
    
class PurchasesByCustomers(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SalesSerializer


    def get(self, request):
        try: 
            customer = request.user.customer_profile
        except Customer.DoesNotExist:
            return Response({"error": "Customer is not associated with any vendor profile."}, status=403)
        
        purchases = Sales.objects.filter(customer=customer)
        serializer = self.serializer_class(purchases, many=True)

        return Response(serializer.data, status=200)
    
class BuyNumberView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        number_ids = request.data.get('number_ids')  # Expect a list of number IDs

        if not number_ids or not isinstance(number_ids, list):
            return Response({"error": "A list of number IDs is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch all numbers and validate
        numbers = Number.objects.filter(id__in=number_ids)
        if len(numbers) != len(number_ids):
            return Response({"error": "One or more number IDs are invalid"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if any number is already sold
        sold_numbers = numbers.filter(is_sold=True)
        if sold_numbers.exists():
            return Response({"error": f"Numbers {', '.join(str(n.id) for n in sold_numbers)} are already sold"}, status=status.HTTP_400_BAD_REQUEST)

        # Check customer profile
        try:
            customer = request.user.customer_profile
        except:
            return Response({"error": "User is not associated with any customer profile"}, status=status.HTTP_403_FORBIDDEN)

        # Calculate total price and collect vendors
        final_price = 0
        vendors = set()
        for number in numbers:
            discounted_price = number.price - (number.price * (number.discount / 100))
            final_price += discounted_price
            vendors.add(number.vendor)

        # Set vendor: None if multiple vendors, or the single vendor if all numbers share the same vendor
        vendor = vendors.pop() if len(vendors) == 1 else None

        # Create the sale
        sale = Sales.objects.create(
            vendor=vendor,
            customer=customer,
            final_price=final_price,
            status='pending',
        )

        # Add numbers to the sale and mark them as sold
        sale.numbers.add(*numbers)
        numbers.update(is_sold=True)

        serializer = SalesSerializer(sale)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    