from django.shortcuts import render, get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response

from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .serializers import CommissionSerializer, CommissionSettingsSerializer, CommissionPriceRange
from .models import CommissionByCategories, CommissionSettings, CommissionByPriceRange
from number.models import Pattern

class CommissionByCategoriesView(generics.ListCreateAPIView):
    serializer_class = CommissionSerializer
    queryset = CommissionByCategories.objects.all()
    permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        pattern = Pattern.objects.filter(id = request.data.get('category')).first()
        if not pattern:
            return Response({"error": "Pattern not found"}, status=status.HTTP_404_NOT_FOUND)
    
        request.data['category'] = pattern.id
        serializer = self.get_serializer(data=request.data)
        print(request.data)
        if (serializer.is_valid()):
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateCommissionView(generics.ListCreateAPIView):
    serializer_class = CommissionSerializer
    
    def post(self, request):
        commission_id = request.data.get('commission_id')
        new_value = request.data.get('commission')
        category_id = request.data.get('category')  # pattern ID
        print(request.data)
        if not all([commission_id, new_value, category_id]):
            return Response({"error": "Missing required fields"}, status=400)

        # Get Commission or 404
        commission = get_object_or_404(CommissionByCategories, id=commission_id)

        # Get Pattern safely
        pattern = Pattern.objects.filter(id=category_id).first()
        if not pattern:

            return Response({"error": "Invalid pattern (category) ID"}, status=400)

        # Update the commission
        commission.value = new_value
        commission.pattern = pattern
        commission.save()

        return Response({"message": "Commission updated successfully"}, status=200)

class CommissionSettingsView(generics.ListCreateAPIView):
    serializer_class = CommissionSettingsSerializer
    queryset = CommissionSettings.objects.all()
    permission_classes = [IsAdminUser]


class NewNumbersCommissionView(generics.ListCreateAPIView):
    serializer_class = CommissionSettingsSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'id'

    def post(self, request, *args, **kwargs):
        new_entries, created = CommissionSettings.objects.get_or_create(id=1)
        new_entries.is_add_on_new_number = True
        new_entries.save()
        return Response({}, status=status.HTTP_200_OK)


class ExistingNumberCommissionView(generics.ListCreateAPIView):
    serializer_class = CommissionSettingsSerializer
    queryset = CommissionSettings.objects.all()
    permission_classes = [IsAdminUser]
    lookup_field = 'id'
    
    def post(self, request):
        existing_entries = self.get_object()
        existing_entries.is_add_on_exist_number = True
        existing_entries.save()
        return Response(status=status.HTTP_200_OK)


class CommissionByPriceRangeView(generics.ListCreateAPIView):
    serializer_class = CommissionPriceRange
    permission_classes = [IsAdminUser]
    queryset = CommissionByPriceRange.objects.all()


class CommissionByPriceRangeDetailView(generics.RetrieveAPIView):
    serializer_class = CommissionPriceRange
    permission_classes = [IsAdminUser]
    queryset = CommissionByPriceRange.objects.all()
    lookup_field = 'id'


class CommissionByPriceRangeUpdateView(generics.UpdateAPIView):
    serializer_class = CommissionPriceRange
    permission_classes = [IsAdminUser]
    queryset = CommissionByPriceRange.objects.all()
    lookup_field = 'id'


class CommissionByPriceRangeDeleteView(generics.DestroyAPIView):
    serializer_class = CommissionPriceRange
    permission_classes = [IsAdminUser]
    queryset = CommissionByPriceRange.objects.all()
    lookup_field = 'id'