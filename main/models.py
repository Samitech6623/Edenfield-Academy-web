from django.db import models
from django.db.models import Sum,Avg
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import apps

# Create your models here.

class Session(models.Model):
    TERM_CHOICES = [
        ("Term 1", "Term 1"),
        ("Term 2", "Term 2"),
        ("Term 3", "Term 3"),
    ]
    
    term = models.CharField(max_length=20, choices=TERM_CHOICES)
    year = models.IntegerField(default=timezone.now().year)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["term", "year"], name="unique_term_year")
        ]
    @property
    def display_name(self):
        return (f"{self.term} Year {self.year}")

    @property
    def is_active(self):
        today = timezone.now().date()
        if self.start_date and self.end_date:
            return self.start_date <= today <= self.end_date
        return False
    @classmethod
    def get_active_session(cls):
  
        today = timezone.now().date()
        try:
            active_session = cls.objects.get(
                start_date__lte=today, 
                end_date__gte=today
            )
            return active_session
        except cls.DoesNotExist:
            pass 
        
        latest_ended_session = cls.objects.filter(
            end_date__lte=today
        ).order_by(
            '-end_date'
        ).first()

        if latest_ended_session:
            return latest_ended_session
        
        return cls.objects.all().order_by('-end_date').first()

    def __str__(self):
        return (f"{self.term} Year {self.year}")



class Management(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name='management')
    is_admin_user = models.BooleanField(default=True)

    def __str__(self):
        return  "school admin"

class Parent(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name='parent')
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(unique=True, null=True, blank=True) 

    @property
    def display_name(self):
        return f"{self.full_name}"
    def __str__(self):
        return (f"parent:{self.full_name}")
    def delete(self, *args, **kwargs):
        # Save reference to the linked user
        linked_user = self.user
        # Delete the Parent record
        super().delete(*args, **kwargs)
        # Delete the linked user too
        if linked_user:
            linked_user.delete()

class Grade(models.Model):
    min_score = models.DecimalField(max_digits=5, decimal_places=2)
    max_score = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=2)
    remark = models.CharField(max_length=50)

    class Meta:
        ordering = ['-min_score']

    @property
    def display_name(self):
        return f"{self.min_score} - {self.max_score} : {self.grade}"

    def clean(self):
        """Ensure min_score is less than max_score."""
        if self.min_score >= self.max_score:
            raise ValidationError(
                'min_score must be strictly less than max_score.'
            )
        # You could also check for negative values if scores must be non-negative
        if self.min_score < 0:
             raise ValidationError('Scores cannot be negative.')

    def save(self, *args, **kwargs):
        if self.grade:
            self.grade = self.grade.upper()
            self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.grade} ({self.min_score}-{self.max_score})"



class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name
    
class ClassRoom(models.Model):
    name = models.CharField(max_length=50, unique=True)
    class_teacher = models.OneToOneField(
        "Teacher", on_delete=models.SET_NULL, null=True, blank=True, related_name="class_teacher"
    )
    description = models.TextField(blank=True, null=True)
    subjects = models.ManyToManyField(Subject, related_name="classes") 

    @property
    def display_name(self):
        return self.name
    @property
    def total_class_students(self):
        return self.students.count()
 

    def __str__(self):
        return self.name

class GradingSystem(models.Model):
    name = models.CharField(max_length=100, unique=True)
    grade_components = models.ManyToManyField(Grade, related_name="grade_components")
    classes = models.ManyToManyField(ClassRoom, blank=True, related_name="grading_systems")
    subjects = models.ManyToManyField(Subject, blank=True, related_name="grading_systems")

    @property
    def display_name(self):
        return self.name


class Student(models.Model):
    parent = models.ForeignKey(Parent,on_delete=models.CASCADE,related_name='children')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=[
        ('Male', 'Male'),
        ('Female', 'Female')
    ])

    admission_number = models.CharField(max_length=20, unique=True)
    enrollment_date = models.DateField()
    current_class = models.ForeignKey(
        ClassRoom, on_delete=models.SET_NULL, null=True, blank=True, related_name="students"
    )   
    is_active = models.BooleanField(default=True)

    @property
    def display_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def exam_summary(self, exam):
       
        results = self.results.filter(exam=exam)
        summary = results.aggregate(total=Sum("score"), average=Avg("score"))
        total = summary["total"] or 0
        average = summary["average"] or 0

        # Fetch the corresponding grade based on the average
        grade_obj = Grade.objects.filter(
            min_score__lte=average, max_score__gte=average
        ).first()

        grade = grade_obj.grade if grade_obj else "-"
        remark = grade_obj.remark if grade_obj else "Ungraded"

        return {
            "total": total,
            "average": round(average, 2),
            "grade": grade,
            "remark": remark,
        }

    
    def total_fees_paid_current_session(self,active_session):
        return self.fee_payment.filter(status="CONFIRMED",paid_on__gte = active_session.start_date).aggregate(total=Sum("amount"))["total"] or 0

    def fee_summary_current_session(self):
        active_session = Session.get_active_session()
        if active_session:
            amount_paid = self.total_fees_paid_current_session(active_session)
            SchoolFeeStructure = apps.get_model("fees", "SchoolFeeStructure")
            try:
                structure = SchoolFeeStructure.objects.get(
                    class_room=self.current_class, session = active_session
                )
                required = structure.total_amount_required
            except SchoolFeeStructure.DoesNotExist:
                required = 0
            balance = required - amount_paid
            return {"balance":balance,"required":required,"amount_paid":amount_paid}
        else:
            return {"balance":0,"required":0,"amount_paid":0}

       
    
    def __str__(self):
        return (f"{self.first_name} {self.last_name} {self.admission_number}") 
    
class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    class_room = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)
    date_enrolled = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'session') # Prevents double enrollment in one term
        ordering = ['-session__year', '-session__term']

    def __str__(self):
        return f"{self.student.full_name} - {self.class_room.name} ({self.session})"
    
class Teacher(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name='teacher')
    teacher_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True, blank=True) 
    phone = models.CharField(max_length=15)

    
    @property
    def display_name(self):
        return (f"{self.teacher_name}")
    
    def __str__(self):
        return self.teacher_name
    
    def subjects_in_class(self, class_obj):
        return Subject.objects.filter(teaching_class_assignments__teacher=self, teaching_class_assignments__class_assigned=class_obj)
    
    def delete(self, *args, **kwargs):
        # Save reference to the linked user
        linked_user = self.user
        # Delete the Parent record
        super().delete(*args, **kwargs)
        # Delete the linked user too
        if linked_user:
            linked_user.delete()



class TeachingClassAssignment(models.Model):
    teacher = models.ForeignKey("Teacher", on_delete=models.CASCADE, related_name="teaching_class_assignments")
    class_assigned = models.ForeignKey("ClassRoom", on_delete=models.CASCADE, related_name="teaching_class_assignments")
    subject = models.ForeignKey("Subject", on_delete=models.CASCADE, related_name="teaching_class_assignments")

    @property
    def display_name(self):
        return f"{self.teacher} teaches {self.subject} in {self.class_assigned}"
    def __str__(self):
        return f"{self.teacher} teaches {self.subject} in {self.class_assigned}"




    

class Exam(models.Model):
    exam_name = models.CharField(max_length=150, blank=False,null=False)
    exam_session = models.ForeignKey(Session,on_delete=models.CASCADE)
    exam_classes = models.ManyToManyField(ClassRoom,related_name="exam_classes")

    class Meta:
        unique_together = ("exam_name", "exam_session")  # ✅ valid combo
        verbose_name_plural = "Exams"

    @property
    def display_name(self):
        return f"{self.exam_name} - {self.exam_session.term} - {self.exam_session.year} Exam"

    def __str__(self):
        return f"{self.exam_name} ({self.exam_session.term} - {self.exam_session.year}) - Exam"

class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="results")
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="exam_details")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    grade_object = models.ForeignKey(
        'Grade', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="results_with_this_grade"
    )    
    remarks = models.TextField(blank=True, null=True)

    @property
    def display_name(self):
        grade_str = self.grade_object.grade if self.grade_object else "N/A"
        return f"{self.student} - {self.subject} ({grade_str})"

    def save(self, *args, **kwargs):
        # Automatically assign grade and remarks based on score
        grade_obj = Grade.objects.filter(min_score__lte=self.score, max_score__gte=self.score).first()
        if grade_obj:
            self.grade_object = grade_obj
        else:
            self.grade_object = None
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.display_name



class Announcement(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()
    author = models.CharField(max_length=100, blank=True, null=True)
    created_on = models.DateTimeField(default=timezone.now)

    @property
    def display_name(self):
        return f"{self.title} - {self.created_on.strftime('%Y-%m-%d')} announcement"

    def __str__(self):
        return f"{self.title} - {self.created_on.strftime('%Y-%m-%d')}"


class Event(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    date = models.DateField()
    location = models.CharField(max_length=255, blank=True, null=True)
    created_on = models.DateTimeField(default=timezone.now)

    @property
    def display_name(self):
        return f"{self.name} ({self.date}) event"

    def __str__(self):
        return f"{self.name} ({self.date})"
    

class Chat(models.Model):
    sender = models.ForeignKey(User, on_delete=models.SET_NULL,null=True, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,related_name='received_messages')
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')
    read_on = models.DateTimeField(null=True,blank=True)

    class Meta:
        ordering = ['-timestamp']

    @property
    def display_name(self):
        sender = self.sender.username if self.sender else "Deleted User"
        receiver = self.receiver.username if self.receiver else "Deleted User"
        return f"From {sender} to {receiver} on {self.timestamp.strftime('%H:%M')}"

    def __str__(self):
        return self.display_name
    

class VisitorMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=10, blank=True, null=True)
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def clean(self):
     if not self.email and not self.phone_number:
            raise ValidationError("Please provide either an email address or a phone number.")
    
    def __str__(self):
        return f"{self.name} - {self.subject or 'No Subject'}"











