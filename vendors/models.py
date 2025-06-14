from django.db import models
from authentication.models import VN_User
import os

def vendor_aadhar_upload_path(instance, filename):
    # Generate path like: vendor_documents/business_name/aadhar/filename
    return os.path.join('vendor_documents', str(instance.business_name), 'aadhar', filename)

def vendor_pan_upload_path(instance, filename):
    # Generate path like: vendor_documents/business_name/pan/filename
    return os.path.join('vendor_documents', str(instance.business_name), 'pan', filename)

def vendor_agreement_upload_path(instance, filename):
    # Generate path like: vendor_documents/business_name/agreement/filename
    return os.path.join('vendor_documents', str(instance.business_name), 'agreement', filename)

class Vendor(models.Model):
    user = models.OneToOneField(VN_User, on_delete=models.CASCADE, related_name="vendor_profile")
    business_name = models.CharField(max_length=255)
    full_address = models.TextField()
    address_area = models.CharField(max_length=255)
    gst_number = models.CharField(max_length=15, null=True, blank=True)
    state = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    aadhar_card = models.FileField(
        upload_to=vendor_aadhar_upload_path,
        max_length=255,
        null=True,
        blank=True,
        help_text="Upload Aadhar card document"
    )
    pan_card = models.FileField(
        upload_to=vendor_pan_upload_path,
        max_length=255,
        null=True,
        blank=True,
        help_text="Upload PAN card document"
    )
    agreement_form = models.FileField(
        upload_to=vendor_agreement_upload_path,
        max_length=255,
        null=True,
        blank=True,
        help_text="Upload signed agreement form"
    )
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.business_name

    def delete(self, *args, **kwargs):
        # Delete the files when the vendor is deleted
        if self.aadhar_card:
            if os.path.isfile(self.aadhar_card.path):
                os.remove(self.aadhar_card.path)
        if self.pan_card:
            if os.path.isfile(self.pan_card.path):
                os.remove(self.pan_card.path)
        if self.agreement_form:
            if os.path.isfile(self.agreement_form.path):
                os.remove(self.agreement_form.path)
        super().delete(*args, **kwargs)



