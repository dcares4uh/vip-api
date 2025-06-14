from django.shortcuts import render
import django_filters
from rest_framework import generics, status
from rest_framework.response import Response
from django.db.models import Q
from django.db.models import Count
import random
from datetime import datetime
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import *
from .models import *
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from vendors.models import Vendor

class GetRandomDataView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = Number.objects.all()
    serializer_class = NumberSerializers
    
    def get(self, request):
        total_count = Number.objects.aggregate(count=Count('id'))['count']
        if total_count == 0:
            return Response({"message": "No numbers available"}, status=200)

        random_numbers = Number.objects.filter(is_sold=False, is_rejected=False).order_by("?")[:30]  # Random 100 records

        serializer = self.get_serializer(random_numbers, many=True)

        return Response(serializer.data, status=200)
    

class NumberDjangoFilters(django_filters.FilterSet):
    entry = django_filters.CharFilter()
    entry_start = django_filters.CharFilter(field_name='entry',lookup_expr='startswith')
    entry_end = django_filters.CharFilter(field_name='entry',lookup_expr='endswith')
    entry_contains = django_filters.CharFilter(field_name='entry',lookup_expr='contains')
    categories = django_filters.ChoiceFilter(choices=NumberType)
    price = django_filters.RangeFilter()
    
    class Meta:
        model = Number
        fields = ['entry', 'entry_start', 'entry_end', 'entry_contains', 'price', 'categories', 'discount']

class NumberFilterAPIView(generics.ListAPIView):
    queryset = Number.objects.all()
    serializer_class = NumberSerializers
    filter_backends = [DjangoFilterBackend]
    filterset_class = NumberDjangoFilters
    permission_classes = [AllowAny]

class NumberListCreateAPIView(generics.ListCreateAPIView):
    queryset = Number.objects.all()
    serializer_class = NumberSerializers
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, *args, **kwargs):
        serializer = NumberSerializers(data=request.data)
        
        if serializer.is_valid():
            if (len(serializer.validated_data['entry']) != 10):
                return Response("Not Valid Number", status=status.HTTP_200_OK)
            
            serializer.save()
            return Response("Created", status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PatternNumbersAPIView(generics.ListAPIView):
    permission_classes = [AllowAny]
    def get(self, request, id):
        pattern = get_object_or_404(Pattern, id=id)
        numbers = pattern.numbers.all()  # thanks to related_name="numbers"
        serializer = NumberSerializers(numbers, many=True)
        return Response({
            "pattern": pattern.pattern,
            "numbers": serializer.data
        }, status=status.HTTP_200_OK)


class NumberUpdateAPIView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Number.objects.all()
    serializer_class = NumberSerializers
    lookup_field = 'id'

    def post(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data
        print(f"Received data for update: {data}")  # Print received data
        
        # Define allowed fields for update with their validators
        allowed_fields = {
            'entry': {
                'type': str,
                'validator': lambda x: len(x) == 10,
                'error': 'Entry must be exactly 10 characters long'
            },
            'pattern': {
                'type': int,
                'validator': lambda x: Pattern.objects.filter(id=x).exists(),
                'error': 'Invalid pattern ID'
            },
            'numberStatus': {
                'type': str,
                'validator': lambda x: x in dict(NumberStatus.choices),
                'error': f'NumberStatus must be one of {[choice[0] for choice in NumberStatus.choices]}'
            },
            'parent_operator': {
                'type': str,
                'validator': lambda x: x in dict(ParentOperator.choices),
                'error': f'ParentOperator must be one of {[choice[0] for choice in ParentOperator.choices]}'
            },
            'circle': {'type': str},
            'price': {
                'type': int,
                'validator': lambda x: x >= 0,
                'error': 'Price must be non-negative'
            },
            'discount': {
                'type': float,
                'validator': lambda x: 0 <= x <= 100,
                'error': 'Discount must be between 0 and 100'
            }
        }

        # Update only allowed fields if they are in the request
        for field, field_info in allowed_fields.items():
            if field in data:
                try:
                    # Convert the value to the expected type
                    value = field_info['type'](data[field])
                    print(f"Processing field {field} with value {value}")  # Print field processing
                    
                    # Special handling for pattern field
                    if field == 'pattern':
                        try:
                            pattern = Pattern.objects.get(id=value)
                            setattr(instance, field, pattern)
                            print(f"Pattern set successfully: {pattern}")  # Print pattern success
                            continue
                        except Pattern.DoesNotExist:
                            error_msg = f"Pattern with id {value} not found"
                            print(f"Error: {error_msg}")  # Print pattern error
                            return Response(
                                {"error": error_msg}, 
                                status=status.HTTP_400_BAD_REQUEST
                            )
                    
                    # Validate the value if a validator is provided
                    if 'validator' in field_info:
                        if not field_info['validator'](value):
                            error_msg = field_info['error']
                            print(f"Validation error for {field}: {error_msg}")  # Print validation error
                            return Response(
                                {"error": error_msg},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                    
                    setattr(instance, field, value)
                    print(f"Field {field} updated successfully")  # Print field update success
                except (ValueError, TypeError) as e:
                    error_msg = f"Invalid value for field {field}: {str(e)}"
                    print(f"Error: {error_msg}")  # Print type conversion error
                    return Response(
                        {"error": error_msg}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

        try:
            instance.save()
            serializer = self.get_serializer(instance)
            print("Number updated successfully")  # Print final success
            return Response({
                "message": "Number updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            error_msg = f"Error saving number: {str(e)}"
            print(f"Error: {error_msg}")  # Print save error
            return Response(
                {"error": error_msg}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
# Delete your views    
class NumberDeleteAPIView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Number.objects.all()
    serializer_class = NumberSerializers
    lookup_field = 'id'  # Changed from 'pk' to 'id' to match URL pattern

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"message": "Deleted Successfully"}, status=status.HTTP_204_NO_CONTENT)


class VendorNumbersAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NumberSerializers
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["entry", "price", "categories"]

    def get_queryset(self):
        """Fetch all numbers for the authenticated vendor"""
        user = self.request.user
        vendor = get_object_or_404(Vendor, user=user)
        return Number.objects.filter(vendor=vendor)

class PatternCreateView(generics.CreateAPIView):
    queryset = Pattern.objects.all()
    serializer_class = PatternSerializers
    permission_classes = [IsAdminUser]

class AdminNumberCreateView(generics.CreateAPIView):
    queryset = Number.objects.all()
    serializer_class = NumberSerializers
    permission_classes = [IsAdminUser]

    def create(self, request, *args, **kwargs):
        vendor_id = request.data.get('vendor')
        pattern_id = request.data.get('pattern')
        
        # Validate vendor
        try:
            vendor = Vendor.objects.get(id=vendor_id)
        except Vendor.DoesNotExist:
            return Response({"error": "Vendor not found."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate pattern
        try:
            pattern = Pattern.objects.get(id=pattern_id)
        except Pattern.DoesNotExist:
            return Response({"error": "Pattern not found."}, status=status.HTTP_400_BAD_REQUEST)

        # Pass the rest of the data to the serializer
        serializer = self.get_serializer(data=request.data)
          
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            print(e.detail)
        
        serializer.save(
            vendor=vendor, 
            pattern=pattern, 
            uploaded_by_admin=True,
            approval_status=True  # Auto-approve admin-created numbers
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

class VendorAddNumbersAPIView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NumberSerializers

    def create(self, request, *args, **kwargs):
        try:
            vendor = Vendor.objects.get(user=request.user)
        except Vendor.DoesNotExist:
            return Response({"error": "Vendor profile not found."}, status=status.HTTP_400_BAD_REQUEST)

        is_vendor_aprroved = vendor.is_approved
        if not is_vendor_aprroved:
            return Response({"error": "Vendor approval require."}, status=status.HTTP_400_BAD_REQUEST)
        
        pattern_id = request.data.get('pattern')
        try:
            pattern = Pattern.objects.get(id=pattern_id)
        except Pattern.DoesNotExist:
            return Response({"error": "Pattern not found."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            vendor=vendor,
            pattern=pattern,
            status=Status.PENDING_APPROVAL,
            approval_status=False  # Set approval_status to False by default
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

class GetNumber(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = NumberSerializers

    def get(self, request, id):
        number = get_object_or_404(Number, id=id)
        
        serializer = self.serializer_class(number)
        return Response(serializer.data, status=200)

class GetAllPatternsView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = Pattern.objects.all()
    serializer_class = PatternSerializers

class GetPatternByIdView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    queryset = Pattern.objects.all()
    serializer_class = PatternSerializers
    lookup_field = 'id'

class PatternDeleteAPIView(generics.DestroyAPIView):
    permission_classes = [IsAdminUser]  # Only admin can delete patterns
    queryset = Pattern.objects.all()
    serializer_class = PatternSerializers
    lookup_field = 'id'

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            "message": "Pattern deleted successfully"
        }, status=status.HTTP_204_NO_CONTENT)

class ApprovedNumbersView(generics.ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = NumberSerializers
    
    def get_queryset(self):
        return Number.objects.filter(approval_status=True)

class UnapprovedNumbersView(generics.ListAPIView):
    permission_classes = [IsAdminUser]  # Only admin should see unapproved numbers
    serializer_class = NumberSerializers
    
    def get_queryset(self):
        return Number.objects.filter(approval_status=False)

class NumberApprovalView(generics.UpdateAPIView):
    permission_classes = [IsAdminUser]
    queryset = Number.objects.all()
    serializer_class = NumberSerializers
    lookup_field = 'id'

    def post(self, request, *args, **kwargs):
        number = self.get_object()
        number.approval_status = True
        number.approval_date = datetime.now()
        number.is_rejected = False
        number.save()
        serializer = self.get_serializer(number)
        return Response({
            "message": "Number approved successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

class NumberRejectionView(generics.UpdateAPIView):
    permission_classes = [IsAdminUser]
    queryset = Number.objects.all()
    serializer_class = NumberSerializers
    lookup_field = 'id'

    def post(self, request, *args, **kwargs):
        number = self.get_object()
        rejection_reason = request.data.get('rejection_reason', '')
        
        # Delete the number since it's rejected
        number.delete()
        
        return Response({
            "message": "Number rejected and removed successfully",
            "rejection_reason": rejection_reason
        }, status=status.HTTP_200_OK)
