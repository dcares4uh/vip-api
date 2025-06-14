from django.db import models
from number.models import Number
from vendors.models import Vendor
from customer.models import Customer
import uuid

class Sales(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numbers = models.ManyToManyField(Number, related_name="number_sales")
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, related_name="sales")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="purchases")
    final_price = models.FloatField()
    status = models.CharField(max_length=20, choices=[("pending", "Pending"), ("completed", "Completed"), ("canceled", "Canceled")], default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.number.entry} sold to {self.customer.user.username} by {self.vendor.user.username if self.vendor else 'Admin'}"
    