from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponseRedirect,HttpResponse,JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView,ListView,UpdateView,CreateView,DeleteView
from django.contrib.auth import login,logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm,PasswordChangeForm,PasswordResetForm
from main.models import Student,Teacher,Parent,ClassRoom,Announcement,Event,Result,Subject,Exam, Session,Grade
from fees.models import SchoolFeeStructure, FeePayment, FeeComponent
from django.urls import reverse_lazy
from django.db.models import Sum,Count,Avg
from django.utils import timezone
from django.db import transaction  # Import transaction for robust saving
from main.utils import (group_student_results, assign_positions,filter_subjects,class_score_summary,handle_own_class_results,
                    handle_other_class_results,subject_results_with_ranks,student_statement,child_latest_exam_summary)

from django.forms import modelformset_factory
from decimal import Decimal

from main.forms import (ParentForm, StudentForm, TeacherForm,ClassRoomForm,FeeStructureForm,
                    FeePaymentForm,ExamSelectionForm, ResultForm,ParentPerformanceFilterForm,
                    FeeStructureSelectionForm)
# Create your views here.
@login_required
def parent_dashboard(request):
    parent = get_object_or_404(Parent, user=request.user)
    children = parent.children.all()
    current_exam = None
    active_session = None

    for child in children:
        child.attendance_rate = getattr(child, "attendance_rate", 95)

        # Get latest exam + fee + performance
        summary = child_latest_exam_summary(child)

        child.latest_exam = summary["exam"]
        child.total_score = summary["total_score"]
        child.average_score = summary["average_score"]
        child.grade = summary["grade"]
        child.remark = summary["remark"]

        if summary["exam"]:
            current_exam = summary["exam"]
            active_session = summary["active_session"]
            child.latest_results = Result.objects.filter(student=child, exam=child.latest_exam)

        # Safely handle fee summary even if active_session is None
        fee_summary = get_fee_summary(child)
        child.balance = fee_summary.get("balance", Decimal("0.00"))
        child.fee_status = fee_summary.get("status", "No Session")
        child.total_required = fee_summary.get("total_required", Decimal("0.00"))
        child.total_paid = fee_summary.get("total_paid", Decimal("0.00"))

    # Get upcoming events
    events = Event.objects.filter(date__gte=timezone.now().date()).order_by("date")[:5]
    announcements = Announcement.objects.all().order_by("-pk")[:5]

    context = {
        "children": children,
        "announcements":announcements,
        "events": events,
        "current_exam": current_exam,
        "active_session": active_session,
    }
    return render(request, "parents/parent_dashboard.html", context)


@login_required
def my_children(request):
    parent = get_object_or_404(Parent, user=request.user)
    children = parent.children.all()   # because of related_name="children"
    return render(request, "parents/my_children.html", {"children": children})


@login_required
def parent_child_detail(request, pk):
    child = get_object_or_404(Student, pk=pk, parent__user=request.user)

    # Example: latest exam results and attendance
    active_session = Session.get_active_session()
    latest_exam = Exam.objects.filter(exam_session=active_session).order_by("-id").first()
    if latest_exam:
        results = Result.objects.filter(student=child, exam=latest_exam)
    else:
        results = Result.objects.none()  # no results found

    fee = child.fee_summary_current_session()  # you can adjust dynamically

    attendance_rate = getattr(child, "attendance_rate", None)

    return render(
        request,
        "parents/parent_child_detail.html",
        {
            "child": child,
            "results": results,
            "latest_exam":latest_exam,
            "total_paid": fee["amount_paid"],
            "balance": fee["balance"],
            "fee_required": fee["required"],
            "active_session":active_session,
            "attendance_rate": attendance_rate,
        },
    )
def parent_performance_page(request):
    form = ParentPerformanceFilterForm(request.GET or None, parent=request.user.parent)

    results = []
    exam_summary = None
    if form.is_valid():
        child = form.cleaned_data["child"]
        if child.parent != request.user.parent:
            messages.error(request,"Sorry!,a parent is allowed to view his/her own child results only")
            return redirect("parent_performance_page")
        else:
            exam = form.cleaned_data["exam"]
            selected_session = form.cleaned_data["session"]
            if exam.exam_session != selected_session:
                messages.error(request, "No results linked with the details provided.Please check and try again")
                return redirect("parent_performance_page")
            else:
                results = Result.objects.filter(student=child, exam=exam).select_related(
                    "subject", "exam__exam_session", "grade_object"
                )
                exam_summary = child.exam_summary(exam)
    return render(request, "parents/parent_children_performance_page.html", {
                "form": form,
                "results": results,
                "exam_summary":exam_summary
            })

'''def parent_download_results(request):
    child_id = request.GET.get("child_id")
    exam_id = request.GET.get("exam_id")

    results = Result.objects.filter(student_id=child_id, exam_id=exam_id).select_related("subject", "grade_object", "exam")

    # Render an HTML template for PDF
    html_string = render(request, "parent/results_pdf.html", {
        "results": results,
        "child": results[0].student if results else None,
        "exam": results[0].exam if results else None,
    }).content.decode("utf-8")

    # Generate PDF
   # pdf_file = HTML(string=html_string).write_pdf()

    #response = HttpResponse(pdf_file, content_type="application/pdf")
    #response['Content-Disposition'] = f'attachment; filename="results_{child_id}_{exam_id}.pdf"'

    return response'''





@login_required
def parent_fees_page(request):
    parent = getattr(request.user, "parent", None)

    if not parent:
        return render(request, "parents/parent_fees_page.html", {"error": "No parent profile found."})

    children = parent.children.all()

    form = FeeStructureSelectionForm()

    return render(request, "parents/parent_fees_page.html", {
        "form": form,
        "children": children
    })

@login_required
def ajax_fee_structure(request):

    student_id = request.GET.get("student")
    session_id = request.GET.get("session")
    class_id = request.GET.get("class")

    fee_structure = SchoolFeeStructure.objects.filter(
        session_id=session_id,
        class_room_id=class_id
    ).first()

    return render(request,"parents/partials/fee_structure.html",{
        "fee_structure":fee_structure
    })

@login_required
def ajax_statement(request):

    student_id = request.GET.get("student")

    context = student_statement(student_id)

    return render(
        request,
        "parents/partials/statement.html",
        context
    )



@login_required
def events_page(request):
    announcements = Announcement.objects.all().order_by("created_on")
    events = Event.objects.filter(date__gte = timezone.now()).order_by("date")  # upcoming first
    return render(request, "parents/events_page.html", {"events": events,"announcements":announcements})

class page_not_available(TemplateView):
    template_name = 'parents/page_not_available.html'

