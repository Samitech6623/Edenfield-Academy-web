from django.shortcuts import render
from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponseRedirect,HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView,ListView,UpdateView,CreateView,DeleteView
from django.contrib.auth import login,logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm,PasswordChangeForm,PasswordResetForm
from main.models import (Student,Teacher,Parent,ClassRoom,Announcement,Event
                         ,Result,Subject,Exam, Session,GradingSystem,Grade,
                         TeachingClassAssignment,Chat,VisitorMessage)
from fees.models import SchoolFeeStructure, FeePayment, FeeComponent
from django.urls import reverse_lazy
from django.db.models import Sum,Count,Avg
from django.utils import timezone
from django.db import transaction  # Import transaction for robust saving
from main.utils import (group_student_results, assign_positions,filter_subjects,class_score_summary,handle_own_class_results,
                    handle_other_class_results,subject_results_with_ranks,get_fee_summary,child_latest_exam_summary)

from django.forms import modelformset_factory


from main.forms import (ParentForm, StudentForm, TeacherForm,ClassRoomForm,FeeStructureForm,SubjectForm,
                    FeePaymentForm,ExamSelectionForm,ExamCreationForm,FeeComponentForm,SessionCreationForm,GradeForm,GradingSystemForm,TeachingClassAssignmentForm)

# Create your views here.
def profile_create(request, form_class, template, go_to_url,role):
    if request.method == "POST":
        user_form = UserCreationForm(request.POST)
        profile_form = form_class(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            return redirect(go_to_url)
    else:
        user_form = UserCreationForm()
        profile_form = form_class()

    return render(request, template, {
        "user_form": user_form,
        "profile_form": profile_form,
        "role":role,
        "go_to_url":go_to_url
    })


@login_required
def management_dashboard(request):
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    total_parents = Parent.objects.count()
    visitors_unread = VisitorMessage.objects.filter(
        is_read = False
        ).count()
    portal_users_unread = Chat.objects.filter(
        receiver=request.user,
        is_read=False
    ).exclude(sender=request.user).count()
    context = {"total_students":total_students,"total_teachers":total_teachers,
               "total_parents":total_parents,"visitors_unread":visitors_unread,
               "portal_users_unread":portal_users_unread}

    return render(request, 'management/base_management_dashboard.html',context=context)

class SettingsPage(TemplateView):
    template_name = 'management/management_settings.html'

@method_decorator(login_required, name='dispatch')
class ManageTeachers(ListView):
    model = Teacher
    template_name = "management/manage_teachers.html"
    context_object_name = "teachers"

class TeacherUpdate(UpdateView):
    model = Teacher
    form_class = TeacherForm
    template_name = "management/add_edit_form.html"
    success_url = reverse_lazy("manage_teachers")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = 'Teacher'
        context['go_to_url'] = 'manage_teachers'

        return context
    
    
class TeacherDelete(DeleteView):
    model = Teacher
    template_name = "management/delete_form.html"
    success_url = reverse_lazy("manage_teachers")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = 'Teacher'
        context['go_to_url'] = 'manage_teachers'

        return context


@method_decorator(login_required, name='dispatch')
class ManageStudents(ListView):
    model = Student
    template_name = "management/manage_students.html"
    context_object_name = "students"


class AddStudent(CreateView):
    model = Student
    form_class = StudentForm
    template_name = "management/add_edit_form.html"
    success_url = reverse_lazy("manage_students")
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = 'Student'
        context['go_to_url'] = 'manage_students'
        context['action'] = 'add'


        return context
    
class StudentUpdate(UpdateView):
    model = Student
    form_class = StudentForm
    template_name = "management/add_edit_form.html"
    success_url = reverse_lazy("manage_students")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = 'Student'
        context['go_to_url'] = 'manage_students'
        context['action'] = 'edit'


        return context

class StudentDelete(DeleteView):
    model = Student
    template_name = "management/delete_form.html"
    success_url = reverse_lazy("manage_students")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = 'Student'
        context['go_to_url'] = 'manage_students'

        return context

   ###
   # PRENTS 

class ManageParents(ListView):
    model = Parent
    template_name = "management/manage_parents.html"
    context_object_name = "parents"

class ParentUpdate(UpdateView):
    model = Parent
    form_class = ParentForm
    template_name = "management/profile_update.html"
    success_url = reverse_lazy("manage_parents")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = 'Parent'
        context['go_to_url'] = 'manage_parents'

        return context
    
    
class ParentDelete(DeleteView):
    model = Parent
    template_name = "management/delete_form.html"
    success_url = reverse_lazy("manage_parents")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = 'Parent'
        context['go_to_url'] = 'manage_parents'


        return context

   ####
   # classes 

@login_required
def manage_classes(request):
    classes = ClassRoom.objects.all().order_by("name")
    return render(request, "management/manage_classes.html", {"classes": classes})

def handle_class(request, action, pk=None):
 
    go_to_url = 'manage_classes'
    if action == "create":
        if request.method == "POST":
            form = ClassRoomForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect("manage_classes")
        else:
            form = ClassRoomForm()
        return render(request, "management/add_edit_form.html", {"form": form, "model_name":'ClassRoom', "action": "Add", "go_to_url":go_to_url})

    elif action == "edit":
        obj = get_object_or_404(ClassRoom, pk=pk)
        if request.method == "POST":
            form = ClassRoomForm(request.POST, instance=obj)
            if form.is_valid():
                form.save()
                return redirect("manage_classes")
        else:
            form = ClassRoomForm(instance=obj)
        return render(request, "management/add_edit_form.html", {"form": form, "model_name":'ClassRoom',  "action": "Edit", "go_to_url":go_to_url})

    elif action == "delete":
        obj = get_object_or_404(ClassRoom, pk=pk)
        if request.method == "POST":
            obj.delete()
            return redirect("manage_classes")
        return render(request, "management/delete_form.html", {"object": obj,"model_name":"ClassRoom","go_to_url":go_to_url})




@method_decorator(login_required, name='dispatch')
class ManageEvents(ListView):
    model = Event
    template_name = "management/manage_events.html"
    context_object_name = "events"   # instead of object_list

    def get_queryset(self):
        # Example: order events by date (soonest first)
        return Event.objects.order_by("date")


@method_decorator(login_required, name='dispatch')
class ManageAnnouncements(ListView):
    model = Announcement
    template_name = "management/manage_announcements.html"
    context_object_name = "announcements" 



def handle_announcement_event(request, model, form_class, template, go_to_url , model_name, action, pk=None):
    obj = None
    if pk:
        obj = get_object_or_404(model, pk=pk)

    if action in ["create", "edit"]:
        if request.method == "POST":
            form = form_class(request.POST, instance=obj)
            if form.is_valid():
                form.save()
                return redirect(go_to_url)
        else:
            form = form_class(instance=obj)
        return render(request, template, {"form": form, "model_name": model_name, "action": action, "go_to_url":go_to_url})

    elif action == "delete":
        if request.method == "POST":
            obj.delete()
            return redirect(go_to_url)
        return render(request, template, {"object": obj, "model_name": model_name, "action": action, "go_to_url":go_to_url})


class ManageFinancials(TemplateView):
    template_name = "management/manage_financials.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["fee_structures"] = SchoolFeeStructure.objects.all()
        context["fees"] = FeePayment.objects.all()
        context["students"] = Student.objects.all()
        return context
    


def handle_fee(request, model, form_class, template, go_to_url, pk=None, action="create", model_name = 'item'):
    if action == "view":
        if request.method == 'GET':
            fee_structure = SchoolFeeStructure.objects.get(pk=pk)
            return render(request,template,{"fee_structure":fee_structure})
        else:
            return redirect(go_to_url)

    elif action == "create":
        if request.method == "POST":
            form = form_class(request.POST)
            if form.is_valid():
                form.save()
                return redirect(go_to_url)
        else:
            form = form_class()
        return render(request, template, {"form": form, "model_name": model_name , "go_to_url":go_to_url, "action":action})

    elif action == "edit":
        obj = get_object_or_404(model, pk=pk)
        if request.method == "POST":
            form = form_class(request.POST, instance=obj)
            if form.is_valid():
                form.save()
                return redirect(go_to_url)
        else:
            form = form_class(instance=obj)
        return render(request, template, {"form": form, "model_name": model_name, "go_to_url":go_to_url, "action":action})

    elif action == "delete":
        obj = get_object_or_404(model, pk=pk)
        if request.method == "POST":
            obj.delete()
            return redirect(go_to_url)
        return render(request, "management/delete_form.html", {"object": obj, "model_name": model_name ,"go_to_url":go_to_url,"action":action})







@login_required
def reports_portal(request):
    # General counts
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    total_parents = Parent.objects.count()

    # Financials
    total_fees_expected = SchoolFeeStructure.objects.aggregate(Sum("total_amount_required"))["total_amount_required__sum"] or 0
    total_fees_paid = FeePayment.objects.aggregate(Sum("amount"))["amount__sum"] or 0
    balance = total_fees_expected - total_fees_paid

    # Activities
    upcoming_events = Event.objects.count()
    announcements_count = Announcement.objects.count()

    context = {
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_parents": total_parents,
        "total_fees_expected": total_fees_expected,
        "total_fees_paid": total_fees_paid,
        "balance": balance,
        "upcoming_events": upcoming_events,
        "announcements_count": announcements_count,
    }
    return render(request, "management/manage_reports.html", context)



@login_required
def management_student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    parent = student.parent.display_name if student.parent else "N/A"

    # Get latest exam summary
    latest_exam_summary = child_latest_exam_summary(student)

    results = None
    if latest_exam_summary['exam']:
        results = Result.objects.filter(
            exam=latest_exam_summary['exam'], 
            student=student
        )

    # Fee summary
    fee_summary = get_fee_summary(student)

    attendance_rate = getattr(student, "attendance_rate", None)

    context = {
        "student": student,
        "exam": latest_exam_summary['exam'],
        "results": results,
        "amount_paid_active_session": fee_summary["amount_paid_active_session"],
        "required_active_session": fee_summary["required_active_session"],
        "balance_active_session": fee_summary["balance_active_session"],
        "overall_paid": fee_summary['total_paid'],
        "overall_required": fee_summary['total_required'],
        "overall_balance": fee_summary['total_balance'],
        "fee_payment_status": fee_summary['status'],
        "attendance_rate": attendance_rate,
        "parent": parent,
    }

    return render(request, 'management/management_models_details.html', context)

class page_not_available(TemplateView):
    template_name = 'management/page_not_available.html'

# map URL key -> (form class, readable name)
FORM_MAP = {
    'exam-model': (ExamCreationForm, 'Exam Model'),
    'session': (SessionCreationForm, 'Academic Session'),
    'fee-component': (FeeComponentForm, 'Fee Component'),
    'grade-component':(GradeForm,'Grade component'),
    'grading-system':(GradingSystemForm,'Grading System'),
    'subject-model':(SubjectForm,'Subject Model'),
    'classroom-model':(ClassRoomForm,'Class Model'),
    'fee-structure':(FeeStructureForm,'Fee Structure'),
    'teaching-assignment-model': (TeachingClassAssignmentForm,'Teacher assigning')
}

def register_setting_item(request, item_type):
    """
    Generic view that handles creation of multiple model types.
    """
    if item_type not in FORM_MAP:
        messages.error(request, "Invalid settings type.")
        return redirect('settings_dashboard')

    form_class, model_name = FORM_MAP[item_type]

    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"{model_name} created successfully ✅")
            return redirect('settings_page')
    else:
        form = form_class()

    context = {
        'form': form,
        'model_name': model_name,
        "go_to_url": "settings_page"
    }
    return render(request, 'management/add_edit_form.html', context)



MODEL_CONFIG = {
    'exam-model': {
        'model': Exam,
        'form': ExamCreationForm,
        'template': 'management/settings/manage_exam_models.html',
        'title': 'Exam Models'
    },
    'grading-system': {
        'model': GradingSystem,
        'form': GradingSystemForm,
        'template': 'management/settings/manage_grading_system.html',
        'title': 'Grading System Models'
    },
    'grade-component': {
        'model': Grade,
        'form': GradeForm,
        'template': 'management/settings/manage_grade_components.html',
        'title': 'Grade Components'
    },
    'session': {
        'model': Session,
        'form': SessionCreationForm,
        'template': 'management/settings/manage_sessions_models.html',
        'title': 'Academic Sessions'
    },
    'subject-model': {
        'model': Subject,
        'form': SubjectForm,
        'template': 'management/settings/manage_subjects.html',
        'title': 'Subjects'
    },
    'teaching-assignment-model': {
        'model': TeachingClassAssignment,
        'form': TeachingClassAssignmentForm,
        'template': 'management/settings/manage_teacher_subjects_assignments.html',
        'title': 'Teaching Assignments'
    },
    'fee-component': {
        'model': FeeComponent,
        'form': FeeComponentForm,
        'template': 'management/settings/manage_fee_structure_components.html',
        'title': 'Fee Components'
    },
    'fee-structure':{
         'model': SchoolFeeStructure,
        'form':  FeeStructureForm,
        'template': 'management/settings/manage_fee_structures.html',
        'title': 'Fee Structures'
    }
}


def view_setting_item(request, item_type):
    """Display all records for a specific settings model."""
    if item_type not in MODEL_CONFIG:
        return render(request, "404.html", status=404)

    # Extract details from MODEL_CONFIG
    model = MODEL_CONFIG[item_type]["model"]
    template = MODEL_CONFIG[item_type]["template"]
    title = MODEL_CONFIG[item_type]["title"]

    # Fetch all objects for that model
    items = model.objects.all()

    context = {
        "title": title,
        "items": items,
        "item_type":item_type,
        "go_to_url":"view_setting_item"
    }
    return render(request, template, context)


def edit_setting_item(request, item_type, pk):
    if item_type not in MODEL_CONFIG:
        return render(request, "404.html", status=404)

    model = MODEL_CONFIG[item_type]["model"]
    form_class = MODEL_CONFIG[item_type]["form"]
    title = MODEL_CONFIG[item_type]["title"]

    instance = get_object_or_404(model, pk=pk)

    if request.method == "POST":
        form = form_class(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect("view_setting_item", item_type=item_type)
    else:
        form = form_class(instance=instance)

    context = {
        "title": f"Edit {title}",
        "form": form,
        "action":'Edit',
        "object": instance,
        "item_type": item_type, 
        "go_to_url": "view_setting_item"
    }
    return render(request, "management/settings/add_edit_form.html", context)

def delete_setting_item(request, item_type, pk):
    """Delete a specific record for a settings model."""
    if item_type not in MODEL_CONFIG:
        return render(request, "404.html", status=404)

    model = MODEL_CONFIG[item_type]["model"]
    title = MODEL_CONFIG[item_type]["title"]

    instance = get_object_or_404(model, pk=pk)

    if request.method == "POST":
        instance.delete()
        return redirect("view_setting_item", item_type=item_type)

    context = {
        "title": f"Delete {title}",
        "object": instance,
        "item_type":item_type,
        "go_to_url":"view_setting_item"
    }
    return render(request, "management/settings/delete_form.html", context)


def visitor_messages(request):
    messages = VisitorMessage.objects.order_by('-created_at')
    return render(request, 'management/visitors_messages.html', {'messages': messages})

def mark_read(request, message_id):
    msg = get_object_or_404(VisitorMessage, id=message_id)
    msg.is_read = True
    msg.save()
    return redirect('visitors_messages')

def mark_unread(request, message_id):
    msg = get_object_or_404(VisitorMessage, id=message_id)
    msg.is_read = False
    msg.save()
    return redirect('visitors_messages')

def delete_message(request, message_id):
    msg = get_object_or_404(VisitorMessage, id=message_id)
    msg.delete()
    return redirect('visitors_messages')

class Message_type(TemplateView):
    template_name = 'management/message_type_selection.html'



