from rest_framework import serializers
from .models import Vendor

class VendorSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source="user.id", read_only=True)  # Fetch UUID of the user

    class Meta:
        model = Vendor
        fields = [
            "user_id", "id", "business_name", "full_address", "address_area",
            "state", "country", "aadhar_card", "pan_card", "agreement_form", "created_at"
        ]
        extra_kwargs = {
            "aadhar_card": {"required": False},
            "pan_card": {"required": False},
            "agreement_form": {"required": False},
        }

    def create(self, validated_data):
        """Ensure a vendor profile is created only once per user"""
        user = self.context["request"].user
        if Vendor.objects.filter(user=user).exists():
            raise serializers.ValidationError("Vendor profile already exists for this user.")
        return Vendor.objects.create(user=user, **validated_data)


class AllVendorSerializers(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    contact = serializers.CharField(source='user.phone')
    total_numbers = serializers.SerializerMethodField()
    class Meta:
        fields = ['id', 'username', 'contact', 'business_name', 'is_approved', 'total_numbers']
        model = Vendor

    def get_total_numbers(self, obj):
        return obj.numbers.count()

        