from django.urls import path
from main.models import Event,Announcement
from fees.models import SchoolFeeStructure, FeePayment, FeeComponent
from main.forms import ParentForm, TeacherForm,FeeStructureForm,FeePaymentForm,EventForm,AnnouncementForm
from . import views  

urlpatterns = [
    path('management/dashboard/', views.management_dashboard, name='management_dashboard'),
    path("portal/management/teachers/", views.ManageTeachers.as_view(), name="manage_teachers"),
    path("portal/management/parents/", views.ManageParents.as_view(), name="manage_parents"),
    path("portal/management/students/", views.ManageStudents.as_view(), name="manage_students"),
    path("portal/management/classes/", views.manage_classes, name="manage_classes"),
    path("portal/management/events/", views.ManageEvents.as_view(), name="manage_events"),
    path("portal/management/announcements/", views.ManageAnnouncements.as_view(), name="manage_announcements"),
        path("portal/management/settings/", views.SettingsPage.as_view(), name="settings_page"),

    path("management/parents/add/", views.profile_create,{"form_class":ParentForm,"template":"management/profile_create.html","go_to_url":"manage_parents","role":"Parent"}, name="parent_add"),
    path("management/parents/edit/<int:pk>/", views.ParentUpdate.as_view(), name="parent_edit"),
    path("management/parents/delete/<int:pk>/", views.ParentDelete.as_view(), name="parent_delete"),


    path("management/classes/add/", views.handle_class, {"action": "create"}, name="class_add"),
    path("management/classes/<int:pk>/edit/", views.handle_class, {"action": "edit"}, name="class_edit"),
    path("management/classes/<int:pk>/delete/", views.handle_class, {"action": "delete"}, name="class_delete"),



    path("management/teachers/add/", views.profile_create,{"form_class":TeacherForm,"template":"management/profile_create.html","go_to_url":"manage_teachers","role":"Teacher"}, name="teacher_add"),
    path("management/teachers/delete/<int:pk>/",views.TeacherDelete.as_view(),name='delete_teacher'),
    path("management/teachers/edit/<int:pk>/",views.TeacherUpdate.as_view(),name='edit_teacher'),




    path("management/students/add/",views.AddStudent.as_view(),name='add_student'),
    path("management/students/delete/<int:pk>/",views.StudentDelete.as_view(),name='delete_student'),
    path("management/students/edit/<int:pk>/",views.StudentUpdate.as_view(),name='edit_student'),

    ###
    ##FINANCES

    path("portal/management/financials/", views.ManageFinancials.as_view(), name="manage_financials"),


     # Fee Structures
     path("management/fees/structures/add/", views.handle_fee,
         {"model": SchoolFeeStructure, "form_class": FeeStructureForm,
          "template": "management/add_edit_form.html", "go_to_url": "manage_financials",
          "model_name": "structure", "action": "create"},
         name="fee_structure_add"),

     path("management/fees/structures/<int:pk>/edit/", views.handle_fee,
         {"model": SchoolFeeStructure, "form_class": FeeStructureForm,
          "template": "management/add_edit_form.html", "go_to_url": "manage_financials",
          "model_name": "structure", "action": "edit"},
         name="fee_structure_edit"),

     path("management/fees/structures/<int:pk>/delete/", views.handle_fee,
         {"model": SchoolFeeStructure, "form_class": FeeStructureForm,
          "template": "management/delete_form.html", "go_to_url": "manage_financials",
          "model_name": "structure", "action": "delete"},
         name="fee_structure_delete"),
     path("management/fees/structures/<int:pk>/view/", views.handle_fee,
         {"model": SchoolFeeStructure,"form_class": None,
          "template": "management/view_fee_structure.html", "go_to_url": "manage_financials",
          "model_name": "fee structure", "action": "view"},
         name="fee_structure_view"),


    # Fee Payments
    path("management/fees/payments/add/", views.handle_fee,
         {"model": FeePayment, "form_class": FeePaymentForm,
          "template": "management/add_edit_form.html", "go_to_url": "manage_financials",
          "model_name": "payment", "action": "create"},
         name="fee_payment_add"),

    path("management/fees/payments/<int:pk>/edit/", views.handle_fee,
         {"model": FeePayment, "form_class": FeePaymentForm,
          "template": "management/add_edit_form.html", "go_to_url": "manage_financials",
          "model_name": "payment", "action": "edit"},
         name="fee_payment_edit"),

    path("management/fees/payments/<int:pk>/delete/", views.handle_fee,
         {"model": FeePayment, "form_class": FeePaymentForm,
          "template": "management/delete_form.html", "go_to_url": "manage_financials",
          "model_name": "payment", "action": "delete"},
         name="fee_payment_delete"),


#Announcements
 path("management/announcements/add/", views.handle_announcement_event,
         {"model": Announcement, "form_class": AnnouncementForm,
          "template": "management/add_edit_form.html", "go_to_url": "manage_announcements",
          "model_name": "announcement", "action": "create"},
         name="announcement_add"),

    path("management/announcements/<int:pk>/edit/", views.handle_announcement_event,
         {"model": Announcement, "form_class": AnnouncementForm,
          "template": "management/add_edit_form.html", "go_to_url": "manage_announcements",
          "model_name": "announcement", "action": "edit"},
         name="announcement_edit"),

    path("management/announcements/<int:pk>/delete/", views.handle_announcement_event,
         {"model": Announcement, "form_class": AnnouncementForm,
          "template": "management/delete_form.html", "go_to_url": "manage_announcements",
          "model_name": "announcement", "action": "delete"},
         name="announcement_delete"),

    # Events
    path("management/events/add/", views.handle_announcement_event,
         {"model": Event, "form_class": EventForm,
          "template": "management/add_edit_form.html", "go_to_url": "manage_events",
          "model_name": "event", "action": "create"},
         name="event_add"),

    path("management/events/<int:pk>/edit/", views.handle_announcement_event,
         {"model": Event, "form_class": EventForm,
          "template": "management/add_edit_form.html", "go_to_url": "manage_events",
          "model_name": "event", "action": "edit"},
         name="event_edit"),

    path("management/events/<int:pk>/delete/", views.handle_announcement_event,
         {"model": Event, "form_class": EventForm,
          "template": "management/delete_form.html", "go_to_url": "manage_events",
          "model_name": "event", "action": "delete"},
         name="event_delete"),


     path("management/reports/", views.reports_portal, name="reports_portal"),
     path("management/students/details/<int:pk>/",views.management_student_detail, name="management_student_detail"),
     path("settings/view/<str:item_type>/", views.view_setting_item, name="view_setting_item"),
     path("settings/register/<str:item_type>/", views.register_setting_item, name="register_setting_item"),
     path("settings/edit/<str:item_type>/<int:pk>/", views.edit_setting_item, name="edit_setting_item"),
     path("settings/delete/<str:item_type>/<int:pk>/", views.delete_setting_item, name="delete_setting_item"),
     path('visitors/messages/', views.visitor_messages, name='visitors_messages'),
     path('visitors/messages/<int:message_id>/read/', views.mark_read, name='mark_read'),
     path('visitors/messages/<int:message_id>/unread/', views.mark_unread, name='mark_unread'),
     path('visitors/messages/<int:message_id>/delete/', views.delete_message, name='delete_message'),
     path('messages/selection/',views.Message_type.as_view(),name='message_type' ),



]