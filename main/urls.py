from django.urls import path
from . import views


urlpatterns = [
    path('home/',views.HomePage.as_view(),name='home'),
    path('about/',views.AboutPage.as_view(),name='about'),
    path('classes/',views.ClassesPage.as_view(),name='classes'),
    path('contact/',views.contact_page_view,name='contact'),
    path('admission/',views.AdmissionPage.as_view(),name='admission'),
    path('FAQs/',views.Faqs.as_view(),name='FAQs'),
    path('gallery/',views.Gallery.as_view(),name='gallery'),
    path('events/',views.Events.as_view(),name='events'),
    path('portal_selection/', views.PortalSelection.as_view(), name='portal_selection'),
    path('portal/login/management/', views.portal_log_in, {"role": "management"}, name='management_portal'),
    path('portal/login/parent/', views.portal_log_in, {"role": "parent"}, name='parent_portal'),
    path('portal/login/teacher/', views.portal_log_in, {"role": "teacher"}, name='teacher_portal'),
    path('portal/logout/', views.logout_view, name='portal_logout'),
    path("page/not/available",views.page_not_available.as_view(),name='page_not_available'),
    #path('chat/delete/', views.DeleteChat.as_view(), name='delete_chat'),



]