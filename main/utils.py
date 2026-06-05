from django.shortcuts import render,redirect,get_object_or_404,reverse
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView,ListView,UpdateView,CreateView,DeleteView
from django.contrib.auth import login,logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm,PasswordChangeForm,PasswordResetForm
from .models import Student,Teacher,Parent,ClassRoom,Announcement,Event,Result,Subject,Exam, Session,Grade
from fees.models import SchoolFeeStructure, FeePayment, FeeComponent,LedgerEntry
from django.urls import reverse_lazy
from django.db.models import Sum,Count,Avg
from django.utils import timezone
from django.db import transaction  # Import transaction for robust saving

from django.forms import modelformset_factory


from .forms import ParentForm, StudentForm, TeacherForm,ClassRoomForm,FeeStructureForm,FeePaymentForm,ExamSelectionForm, ResultForm
from collections import defaultdict
from decimal import Decimal

def group_student_results(results_qs, students):
    grouped = []
    student_results_map = defaultdict(list)
    class_total = 0

    for result in results_qs:
        student_results_map[result.student_id].append(result)

    for student in students:
        results = student_results_map.get(student.id, [])
        if not results:
            continue
        total = sum(r.score for r in results)
        average = round(total / len(results), 2)
        grade_obj = Grade.objects.filter(min_score__lte=average, max_score__gte=average).first()
        grade = grade_obj.grade if grade_obj else "-"
        remark = grade_obj.remark if grade_obj else "No remark"

        grouped.append({
            "student": student,
            "records": results,
            "total": total,
            "average": average,
            "grade": grade,
            "remark": remark,
        })

    return grouped

def assign_positions(grouped_data):
    grouped_data.sort(key=lambda x: x["average"], reverse=True)
    for idx, data in enumerate(grouped_data, start=1):
        data["position"] = idx
    return grouped_data


def filter_subjects(grouped_data, subjects_taught):
    filtered = []
    for data in grouped_data:
        data["records"] = [r for r in data["records"] if r.subject in subjects_taught]
        if data["records"]:
            filtered.append(data)
    return filtered

def class_score_summary(grouped_data,results_qs):
    totals = [entry["total"] for entry in grouped_data]

    class_mean_score = round(sum(totals) / len(totals), 2) if totals else None
    


        # 2. class_mean_grade: based on class_mean_score

    class_average = results_qs.aggregate(avg=Avg("score"))["avg"]
    class_average = round(class_average, 2) if class_average else None

    if class_average is not None:
        grade_obj = Grade.objects.filter(min_score__lte=class_average, max_score__gte=class_average).first()
        class_mean_grade = grade_obj.grade if grade_obj else "-"
    else:
        class_mean_grade = None
    subject_means_qs = results_qs.values("subject__name").annotate(mean_score=Avg("score"))
    class_subject_mean = { }
    for entry in subject_means_qs:
        subject_name = entry["subject__name"]
        mean_score = round(entry["mean_score"], 2)
        
        # Get grade for the mean score
        grade_obj = Grade.objects.filter(min_score__lte=mean_score, max_score__gte=mean_score).first()
        grade = grade_obj.grade if grade_obj else "-"
        class_subject_mean[subject_name] = {
                    "mean_score": mean_score,
                    "mean_grade": grade,
                }
            

    grouped = {
        "class_mean_score":class_mean_score,
        "class_average":class_average,
    "class_mean_grade":class_mean_grade,
        "class_subjects_mean":class_subject_mean

    }

    return grouped


def subject_results_with_ranks(grouped_data, subjects_taught):
    subjects_data = defaultdict(list)

    # Go through each student's records
    for student_data in grouped_data:
        for result in student_data["records"]:
            if result.subject in subjects_taught:
                subjects_data[result.subject.name].append({
                    "student": result.student,
                    "score": result.score,
                    "grade": result.grade_object.grade,
                    "remark": result.grade_object.remark,
                })

    ranked_subjects = []

    for subject, results in subjects_data.items():
        results = sorted(results, key=lambda x: x["score"], reverse=True)

        for idx, res in enumerate(results, start=1):
            res["rank"] = idx

        mean_score = sum(r["score"] for r in results) / len(results)
        grade_obj = Grade.objects.filter(
            min_score__lte=mean_score,
            max_score__gte=mean_score
        ).first()

        ranked_subjects.append({
            "subject": subject,
            "mean_score": round(mean_score, 2),
            "mean_grade": grade_obj.grade if grade_obj else "N/A",
            "remark": grade_obj.remark if grade_obj else "",
            "records": results,
        })

    return ranked_subjects


def get_or_create_results_for_class(exam, students, subjects):
    for student in students:
        for subject in subjects:
            Result.objects.get_or_create(student=student, subject=subject, exam=exam)
    return Result.objects.filter(exam=exam, student__in=students)


def handle_own_class_results(request, exam, selected_class, students,exam_session):
    subjects = selected_class.subjects.all()
    results = Result.objects.filter(exam=exam, student__in=students)

    expected_count = students.count() * subjects.count()
    if not results.exists() or results.count() < expected_count:
        results = get_or_create_results_for_class(exam, students, subjects)

    ExamResultFormSet = modelformset_factory(Result, form=ResultForm, extra=0)
    formset = ExamResultFormSet(request.POST or None, queryset=results, prefix="own")

    if request.method == "POST" and formset.is_valid():
        try:
            with transaction.atomic():
                formset.save()
            messages.success(request, "✅ My Class grades saved successfully!")

            return redirect(f"{reverse('teacher_students_grades_view')}?session={exam_session.id}&exam={exam.id}&class_selected={selected_class.id}")
           # return redirect ('teacher_students_grades_view')
        except Exception as e:
            messages.error(request, f"❌ Database Error during save: {e}")

    return formset


def handle_other_class_results(request, exam, selected_class, students, subjects_taught,exam_session):
    subjects = selected_class.subjects.all()
    all_results = Result.objects.filter(exam=exam, student__in=students)

    expected_count = students.count() * subjects.count()
    if not all_results.exists() or all_results.count() < expected_count:
        all_results = get_or_create_results_for_class(exam, students, subjects)
    results = Result.objects.filter(
        exam=exam,
        student__in=students,
        subject__in=subjects_taught
    )
    ExamResultFormSet = modelformset_factory(Result, form=ResultForm, extra=0)
    formset = ExamResultFormSet(request.POST or None, queryset=results, prefix="other")

    if request.method == "POST" and formset.is_valid():
        try:
            with transaction.atomic():
                formset.save()
            messages.success(request, "✅ Grades for other classes updated successfully!")

            return redirect(f"{reverse('teacher_students_grades_view')}?session={exam_session.id}&exam={exam.id}&class_selected={selected_class.id}")

        except Exception as e:
            messages.error(request, f"❌ Database Error during save: {e}")

    return formset

def student_statement( student_id):
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
    return context

def get_fee_summary(student):
    # Get current session object
    current_session = Session.get_active_session()

    if not current_session:
        return {
            "required": Decimal("0.00"),
            "paid": Decimal("0.00"),
            "balance": Decimal("0.00"),
            "status": "No Session",
        }

    # 1. Get ALL sessions up to and including the selected session
    fee_sumary_active_session = student.fee_summary_current_session()
    all_relevant_sessions = Session.objects.filter(
        year__lt=current_session.year
    ) | Session.objects.filter(
        year=current_session.year, term__lte=current_session.term
    )

    # 2. Total required for ALL relevant sessions (past and current)
    all_fees = SchoolFeeStructure.objects.filter(
        class_room=student.current_class,
        session__in=all_relevant_sessions
    )

    # Sum the stored 'total_amount_required' field (assuming this is kept updated by signals)
    total_required = all_fees.aggregate(total=Sum("total_amount_required"))["total"] or Decimal("0.00")

    # 3. Total paid so far (for all time)
    total_paid = FeePayment.objects.filter(
        student=student,
        status="CONFIRMED"
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    # 4. Calculate balance (Positive: owed, Negative: overpaid)
    balance = total_required - total_paid

    # 5. Determine status
    if balance <= 0:
        status = "Paid in Full" if balance == 0 else "Overpaid"
    elif total_paid == 0:
        status = "Not Paid"
    else:
        status = "Partially Paid"

    # Return the correct balance sign: positive (owed) or negative (credit)
    return {
        "required_active_session": fee_sumary_active_session['required'],
        "balance_active_session": fee_sumary_active_session['balance'],
        "amount_paid_active_session": fee_sumary_active_session['amount_paid'],
        "total_required": total_required,
        "total_paid": total_paid,
        "total_balance": balance, 
        "status": status,
    }



def child_latest_exam_summary(child):
    # Get active session
    active_session = Session.get_active_session()

    if not active_session:
        return {
            "active_session": active_session,
            "exam": None,
            "total_score": 0,
            "average_score": 0,
            "grade": "-",
            "remark": "No active session"
        }

    # Get the latest exam in that session
    exam = Exam.objects.filter(exam_session=active_session).order_by('-id').first()

    if not exam:
        return {
            "active_session": active_session,
            "exam": None,
            "total_score": 0,
            "average_score": 0,
            "grade": "-",
            "remark": "No exam yet"
        }

    summary = child.exam_summary(exam)

    return {
        "active_session": active_session,
        "exam": exam,
        "total_score": summary["total"],
        "average_score": summary["average"],
        "grade": summary["grade"],
        "remark": summary["remark"],
    }

