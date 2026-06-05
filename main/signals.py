from django.db.models.signals import m2m_changed,post_save
from django.dispatch import receiver
from .models import Enrollment
from main.models import Student, Session
from fees.models import SchoolFeeStructure , LedgerEntry, FeePayment

# Signal to capture when components are added/removed from a structure
@receiver(m2m_changed, sender=SchoolFeeStructure.components.through)
def update_total_on_m2m_change(sender, instance, action, **kwargs):
    """
    Triggers recalculation when a component is added, removed, or cleared 
    from a SchoolFeeStructure instance.
    """
    # Only act on actions that change the composition of the total
    if action in ['post_add', 'post_remove', 'post_clear']:
        # 'instance' here is the SchoolFeeStructure object
        instance.calculate_total_amount_required()



@receiver(post_save, sender=Student)
def track_student_enrollment(sender, instance, created, **kwargs):
    active_session = Session.get_active_session() # Use your existing method
    
    if active_session and instance.current_class:
        # Update or create the history for this session
        Enrollment.objects.get_or_create(
            student=instance,
            session=active_session,
            defaults={'class_room': instance.current_class}
        )


@receiver(post_save, sender=Enrollment)
def record_fee_debit(sender, instance, created, **kwargs):
    """When a student is enrolled, bill them based on the Fee Structure."""
    if created:
        structure = SchoolFeeStructure.objects.filter(
            class_room=instance.class_room,
            session=instance.session
        ).first()

        if structure:
            LedgerEntry.objects.create(
                student=instance.student,
                entry_type="DEBIT",
                payment_method = "STANDARD INVOICE",
                amount=structure.total_amount_required,
                description=f"Fees for {instance.session.term} {instance.session.year} ({instance.class_room.name})"
            )

@receiver(post_save, sender=FeePayment)
def record_payment_credit(sender, instance, **kwargs):
    """When a payment is confirmed, add it to the ledger as a credit."""
    if instance.status == "CONFIRMED":
        # Check if this payment was already recorded to avoid duplicates
        exists = LedgerEntry.objects.filter(receipt_number=instance.receipt_number).exists()
        
        if not exists:
            LedgerEntry.objects.create(
                student=instance.student,
                entry_type="CREDIT",
                amount=instance.amount,
                payment_method=instance.payment_method,
                receipt_number=instance.receipt_number,
                description=f"Fee Payment - {instance.receipt_number}"
            )