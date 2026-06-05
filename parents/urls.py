from django.urls import path
from . import views

urlpatterns = [
        path('parent/dashboard/', views.parent_dashboard, name='parent_dashboard'),
        path("parent/children/", views.my_children, name="my_children"),
        path("child/<int:pk>/", views.parent_child_detail, name="child_detail"),
        path("parent/events/", views.events_page, name="events_page"),
        path("parent/performance/",views.parent_performance_page, name="parent_performance_page"),
        path("parent/fees/", views.parent_fees_page, name="parent_fees_page"),
        path("parents/ajax/fee-structure/", views.ajax_fee_structure, name="ajax_fee_structure"),
        path("parents/ajax/statement/", views.ajax_statement, name="ajax_statement"),
]