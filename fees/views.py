from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from main.models import Student  # import your Student model
from .models import LedgerEntry
# Create your views here.
# fees/views.py


def student_statement(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    entries = LedgerEntry.objects.filter(student=student).order_by('date')

    balance = 0
    total_paid = 0
    statement_entries = []

    for entry in entries:
        if entry.entry_type == "DEBIT":
            balance += entry.amount
        elif entry.entry_type in ["CREDIT", "REFUND"]:
            balance -= entry.amount
            if entry.entry_type == "CREDIT":
                total_paid += entry.amount

        statement_entries.append({
            'date': entry.date,
            'description': entry.description,
            'debit': entry.amount if entry.entry_type == "DEBIT" else None,
            'credit': entry.amount if entry.entry_type in ["CREDIT", "REFUND"] else None,
            'balance': balance,
            'receipt_number': entry.receipt_number,
            'payment_method': entry.payment_method,
        })

    context = {
        'student': student,
        'statement_entries': statement_entries,
        'final_balance': balance,
        'total_paid': total_paid,
        'status': "Cleared" if balance <= 0 else "Owing"
    }
    return render(request, 'fees/fee_statement.html', context)