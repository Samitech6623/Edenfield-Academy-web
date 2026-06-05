from django.db import models
from main.models import ClassRoom, Session, Student
from django.utils import timezone
from django.db.models import Sum

# Create your models here.


class FeeComponent(models.Model):
    name = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    @property
    def display_name(self):
        return f"{self.name}: {self.amount}"
    def __str__(self):
        return f"{self.name}: {self.amount}"

class SchoolFeeStructure(models.Model):
    class_room = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name="fee_structures")
    session = models.ForeignKey(Session,on_delete = models.CASCADE)
    components = models.ManyToManyField(FeeComponent, related_name='fee_structures')
    total_amount_required = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def display_name(self):
        return f"{self.class_room.name} -- {self.session.term} -- {self.session.year} fee structure"
    def calculate_total_amount_required(self):
        total = self.components.aggregate(total=Sum('amount'))['total'] or 0
        self.total_amount_required = total
        self.save(update_fields=['total_amount_required']) # Only update the total field

    def __str__(self):
        return f"{self.class_room} - {self.session.term} {self.session.year} - {self.total_amount_required}"
    
class FeePayment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="fee_payment")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_on = models.DateTimeField(default=timezone.now)
    receipt_number = models.CharField(max_length=50, unique=True)  # M-Pesa receipt
    payment_method = models.CharField(max_length=20, choices=[
        ("MPESA", "M-Pesa"),
        ("BANK", "Bank"),
        ("CASH", "Cash"),
    ], default="MPESA")
    status = models.CharField(max_length=20, choices=[
        ("PENDING", "Pending"),
        ("CONFIRMED", "Confirmed"),
        ("FAILED", "Failed"),
    ], default="PENDING")

    @property
    def display_name(self):
        return f"{self.student} - {self.amount} ({self.receipt_number}) payment"

    def __str__(self):
        return f"{self.student} - {self.amount} ({self.status})"



class LedgerEntry(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="ledger_entries")
    date = models.DateTimeField(default=timezone.now)

    entry_type = models.CharField(max_length=20, choices=[
        ("DEBIT", "Debit"),
        ("CREDIT", "Credit"),
        ("ADJUSTMENT", "Adjustment"),
        ("REFUND", "Refund"),
        ("DISCOUNT", "Discount"),
    ])

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    payment_method = models.CharField(max_length=20, choices=[
        ("STANDARD INVOICE", "standard invoice"),
        ("MPESA", "M-Pesa"),
        ("BANK", "Bank"),
        ("CASH", "Cash"),
    ], null=True, blank=True)

    receipt_number = models.CharField(max_length=50, null=True, blank=True)

    description = models.CharField(max_length=255, null=True, blank=True)  # optional narrative

    def __str__(self):
        return f"{self.student} - {self.entry_type} - {self.amount}"