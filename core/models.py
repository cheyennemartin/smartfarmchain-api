from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    ROLE_CHOICES = [
        ("ADMIN", "Admin"),
        ("RESEARCH_ORG", "Research Org"),
        ("FARMER", "Farmer"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="FARMER")
    wallet_address = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class Harvest(models.Model):
    farmer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    batch_id = models.CharField(max_length=100, unique=True)
    farm_name = models.CharField(max_length=255)
    crop_type = models.CharField(max_length=100)
    harvest_weight_kg = models.DecimalField(max_digits=10, decimal_places=2)
    harvest_date = models.DateField()
    field_location = models.CharField(max_length=255)

    approval_status = models.CharField(max_length=20, default="PENDING")
    payment_status = models.CharField(max_length=20, default="PENDING")

    suspicious_flag = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)


class IoTReading(models.Model):
    harvest = models.ForeignKey(Harvest, on_delete=models.CASCADE)
    temperature = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    soil_moisture = models.FloatField(null=True, blank=True)
    ndvi = models.FloatField(null=True, blank=True)
    anomaly_flag = models.BooleanField(default=False)


class Approval(models.Model):
    harvest = models.ForeignKey(Harvest, on_delete=models.CASCADE)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    approval_action = models.CharField(max_length=20)
    notes = models.TextField(blank=True)


class Payment(models.Model):
    harvest = models.ForeignKey(Harvest, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, default="PENDING")
    wallet_address = models.CharField(max_length=255, blank=True)
    transaction_hash = models.CharField(max_length=255, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)


class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=100)
    result = models.CharField(max_length=50)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)