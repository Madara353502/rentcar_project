from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomUserChangeForm
from cars.forms import ClientForm
from cars.models import Client
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
import pytz

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile(request):
    try:
        client = request.user.client
    except Client.DoesNotExist:
        client = None

    if request.method == 'POST':
        user_form = CustomUserChangeForm(request.POST, instance=request.user)
        client_form = ClientForm(request.POST, instance=client)
        
        if user_form.is_valid() and client_form.is_valid():
            user_form.save()
            if client_form.has_changed():
                client = client_form.save(commit=False)
                client.user = request.user
                client.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = CustomUserChangeForm(instance=request.user)
        client_form = ClientForm(instance=client)
    
    return render(request, 'registration/profile.html', {
        'user_form': user_form,
        'client_form': client_form,
        'client': client
    })

@require_POST
@ensure_csrf_cookie
def set_timezone(request):
    try:
        timezone = request.POST.get('timezone')
        if timezone in pytz.all_timezones:
            request.session['django_timezone'] = timezone
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': 'Invalid timezone'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_http_methods(["POST"])
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home') 