# fees/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('student/<int:student_id>/statement/', views.student_statement, name='student_statement'),
]