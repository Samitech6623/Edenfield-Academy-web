from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import (Parent, Student, Teacher,ClassRoom,User,
        Announcement, Event,Session, Exam, Result,Grade,Subject,
        GradingSystem,TeachingClassAssignment,Chat,VisitorMessage)
from fees.models import SchoolFeeStructure, FeePayment, FeeComponent


class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username" , "password1", "password2"]

class ParentForm(forms.ModelForm):
    class Meta:
        model = Parent
        fields = ["full_name", "phone", "email"]


class ParentForm(forms.ModelForm):
    class Meta:
        model = Parent
        fields = [ "full_name", "phone","email"]

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'

        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
             'enrollment_date': forms.DateInput(attrs={'type': 'date'}),
        }


class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = [ "teacher_name" , "email" , "phone" ]

class ClassRoomForm(forms.ModelForm):
    class Meta:
        model = ClassRoom
        fields = '__all__'

        widgets = {
            "subjects":forms.CheckboxSelectMultiple()
        }

class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = SchoolFeeStructure
        fields = ["class_room","session","components"]
        widgets = {
            "components": forms.CheckboxSelectMultiple(attrs={'class':'multiple-input-container'})
        }

        
class FeePaymentForm(forms.ModelForm):
    class Meta:
        model = FeePayment
        fields = '__all__'
        widgets = {
            'paid_on': forms.DateInput(attrs={'type':'date'})
        }




class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = '__all__'

        widgets = {
            'created_on': forms.DateInput(attrs={'type':'date'})
        }

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = '__all__'

        widgets = {
            'date': forms.DateInput(attrs={'type':'date'}),
            'created_on': forms.DateInput(attrs={'type':'date'})
        }


class ExamSelectionForm(forms.Form):
    session = forms.ModelChoiceField(
        queryset=Session.objects.all(),
        label="Select Session",
        widget=forms.Select(attrs={"class": "form-control"})
    )
    exam = forms.ModelChoiceField(
        queryset=Exam.objects.all(),
        label="Select Exam",
        widget=forms.Select(attrs={"class": "form-control"})
    )
    class_selected = forms.ModelChoiceField(
        queryset=ClassRoom.objects.all(),
        label="Select Class",
        widget=forms.Select(attrs={"class": "form-control"})
    )

class ResultForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = ['student', 'subject', 'score', 'remarks']
        
        widgets = {
            'student': forms.HiddenInput(),
            'subject': forms.HiddenInput(),
            'score': forms.NumberInput(attrs={'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = '__all__'

class GradingSystemForm(forms.ModelForm):
    class Meta:
        model = GradingSystem
        fields = '__all__'

class ParentPerformanceFilterForm(forms.Form):
    child = forms.ModelChoiceField(queryset=None)
    session = forms.ModelChoiceField(queryset=Session.objects.all())
    exam = forms.ModelChoiceField(queryset=Exam.objects.all())

    def __init__(self, *args, **kwargs):
        parent = kwargs.pop("parent")
        super().__init__(*args, **kwargs)
        self.fields["child"].queryset = Student.objects.filter(parent=parent)

class FeeStructureSelectionForm(forms.Form):
    session = forms.ModelChoiceField(
        queryset=Session.objects.all(),
        label="Select Session",
        widget=forms.Select(attrs={"class": "form-control"})
    )
    class_room = forms.ModelChoiceField(queryset=ClassRoom.objects.all().order_by('name'),
        label="Select Class",
        widget=forms.Select(attrs={"class": "form-control"})
        )
    
class FeeComponentForm(forms.ModelForm):
    class Meta:
        model = FeeComponent
        fields = "__all__"

class ExamCreationForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = "__all__"
        widget = {
        "exam_classes":forms.CheckboxSelectMultiple()
        }

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = "__all__"

class SessionCreationForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = "__all__"
        widgets = {
            "start_date":forms.DateInput(attrs={'type': 'date'}),
            "end_date":forms.DateInput(attrs={'type': 'date'})
        }
class TeachingClassAssignmentForm(forms.ModelForm):
    class Meta:
        model = TeachingClassAssignment
        fields = "__all__"

class VisitorMessageForm(forms.ModelForm):
    class Meta:
        model = VisitorMessage
        fields = ['name', 'email', 'phone_number', 'subject', 'message']
        widgets = {
                    'name': forms.TextInput(attrs={'placeholder': 'Your Full Name'}),
                    'email': forms.EmailInput(attrs={'placeholder': 'Your Email Address (optional)'}),
                    'phone_number': forms.TextInput(attrs={'placeholder': 'Your Phone Number (optional)'}),
                    'subject': forms.TextInput(attrs={'placeholder': 'Subject of Your Message'}),
                    'message': forms.Textarea(attrs={'placeholder': 'Write Your Message Here'}),
                }
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            if not phone_number.isdigit():
                raise forms.ValidationError("Phone number must contain only digits.")
            if len(phone_number) != 10:  # Optional: Check for exactly 10 digits
                raise forms.ValidationError("Phone number must be 10 digits.")
        return phone_number

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        phone_number = cleaned_data.get('phone_number')
        
        if not email and not phone_number:
            raise forms.ValidationError("Please provide either an email address or a phone number.")
        
        return cleaned_data


    
