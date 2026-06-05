from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from main.models import Chat
from django.contrib.auth.decorators import login_required


User = get_user_model()

@login_required
def chat_room(request, username):
    """
    Renders the chat interface and dynamically selects the base template 
    based on the URL path used to access the view.
    """
    # 1. Fetch the user the logged-in user wants to chat with
    receiver = get_object_or_404(User, username=username)
    
    # 2. Retrieve the message history between the two users
    messages = Chat.objects.filter(
        sender__in=[request.user, receiver],
        receiver__in=[request.user, receiver]
    ).order_by("timestamp")

    # 3. Identify the last message ID for AJAX/Polling updates
    last_message_id = messages.last().id if messages.exists() else 0

    # 4. DYNAMIC TEMPLATE SELECTION
    # We look at request.path to see which 'folder' the user is in.
    current_path = request.path

    if "/management/" in current_path:
        base_template = "management/base_management_dashboard.html"
    elif "/teachers/" in current_path:
        base_template = "teachers/teacher_dashboard.html"
    elif "/parents/" in current_path:
        base_template = "parents/parent_dashboard.html"
    else:
        # Fallback for general site access (e.g., /chat/username/)
        base_template = "main/base.html"

    # 5. Build the Context
    context = {
        "receiver": receiver,
        "messages": messages,
        "last_message_id": last_message_id,
        "base_template": base_template, # Passed to {% extends base_template %}
        "tab": "internal",              # Helps set 'active' class on tabs
    }

    return render(request, "chat/chat_room.html", context)