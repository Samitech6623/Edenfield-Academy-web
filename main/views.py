from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponseRedirect,HttpResponse,JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView,ListView,UpdateView,CreateView,DeleteView
from django.contrib.auth import login,logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm,PasswordChangeForm,PasswordResetForm
from .models import Event,Chat
from .forms import VisitorMessageForm



def portal_log_in(request,role):
    if request.method == 'POST':
        form = AuthenticationForm( request,data = request.POST )
        if form.is_valid():
            user = form.get_user()
            if hasattr(user,role):
                login(request,user)
                return redirect(f'{role}_dashboard')
            else:
               messages.error(request, f"No {role} account with those details. Please try again or select another dashboard.")
        else:
            messages.error(request, "Invalid username or password.")

    else:
        form = AuthenticationForm()
    return render(request,'main/log_in_form.html',{"form":form,"role":role})

def logout_view(request):
    logout(request)
    return redirect('portal_selection')

class page_not_available(TemplateView):
    template_name = 'dashboards/page_not_available.html'

class AboutPage(TemplateView):
    template_name = 'main/about.html'

class HomePage(TemplateView):
    template_name = 'main/home.html'

class ClassesPage(TemplateView):
    template_name = 'main/classes.html'
    
def contact_page_view(request):
    if request.method == 'POST':
        form = VisitorMessageForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('contact')
    else:
        form = VisitorMessageForm()

    return render(request, 'main/contact.html', {'form': form})



class AdmissionPage(TemplateView):
    template_name = 'main/admission.html'

class Faqs(TemplateView):
    template_name = 'main/FAQs.html'

class Gallery(TemplateView):
    template_name = 'main/gallery.html'

class Events(TemplateView):
    template_name = 'main/events.html'
class PortalSelection(TemplateView):
    template_name = 'main/portal_selection.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        user_role = None
        if user.is_authenticated:
            if hasattr(user, 'teacher'):
                user_role = 'teacher'
            elif hasattr(user, 'parent'):
                user_role = 'parent'
            elif hasattr(user, 'management'):
                user_role = 'management'
        context['user_role'] = user_role
        return context






