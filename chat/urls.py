# chat/urls.py
from django.urls import path
from . import views


# We don't necessarily need app_name here if we define 
# the namespace in the project-level include()
urlpatterns = [
    # This matches the 'username' from the dashboard link
    path('<str:username>/', views.chat_room, name='chat_room'),
]