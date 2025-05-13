import logging

from django.shortcuts import render, redirect
from django.contrib import auth, messages
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch

from orders.models import Order, OrderItem
from .forms import UserLoginForm, UserRegistrationForm, ProfileForm, UserTimezoneForm, UserNoteForm, UserGroupForm
from .models import UserNote, UserGroup, UserTimezone


logger = logging.getLogger(__name__)

def login(request):
    logger.info(f"Processing login request from IP: {request.META.get('REMOTE_ADDR')}")
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        logger.debug(f"Login form submitted with data: {request.POST}")
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = auth.authenticate(username=username,
                                     password=password)
            auth.login(request, user)
            logger.info(f"User '{username}' logged in successfully.")
            return HttpResponseRedirect(reverse('main:product_list'))
        else:
            logger.warning(f"Invalid login form data from IP: {request.META.get('REMOTE_ADDR')}. Errors: {form.errors}")
            messages.error(request, 'Invalid username or password')
    else:
        form = UserLoginForm()
        logger.info("Displaying login form.")
    return render(request, 'users/login.html', {'form': form})


def registration(request):
    logger.info(f"Processing registration request from IP: {request.META.get('REMOTE_ADDR')}")
    if request.method == 'POST':
        form = UserRegistrationForm(data=request.POST)
        logger.debug(f"Registration form submitted with data: {request.POST}")
        if form.is_valid():
            user = form.save()
            auth.login(request, user)
            logger.info(f"User '{user.username}' registered successfully from IP: {request.META.get('REMOTE_ADDR')}.")
            messages.success(
                request, f'{user.username}, Successful Registration'
            )
            return HttpResponseRedirect(reverse('user:login'))
        else:
            logger.warning(f"Invalid registration form data from IP: {request.META.get('REMOTE_ADDR')}. Errors: {form.errors}")
            messages.error(request, 'Please correct the registration errors.')
    else:
        form = UserRegistrationForm()
        logger.info("Displaying registration form.")
    return render(request, 'users/registration.html', {'form': form})

@login_required
def profile(request):
    logger.info(f"Displaying profile for user '{request.user.username}' (ID: {request.user.id}).")
    profile_form = ProfileForm(instance=request.user)
    try:
        timezone_info = request.user.timezone_info
        logger.debug(f"User '{request.user.username}' has timezone info: {timezone_info.timezone}")
    except UserTimezone.DoesNotExist:
        timezone_info = UserTimezone(user=request.user)
        logger.debug(f"User '{request.user.username}' does not have timezone info, creating default.")
    timezone_form = UserTimezoneForm(instance=timezone_info)
    note_form = UserNoteForm()
    group_form = UserGroupForm()

    if request.method == 'POST':
        if 'profile_submit' in request.POST:
            profile_form = ProfileForm(data=request.POST, instance=request.user, files=request.FILES)
            logger.debug(f"Profile update form submitted by user '{request.user.username}' with data: {request.POST} and files: {request.FILES}")
            if profile_form.is_valid():
                profile_form.save()
                logger.info(f"Profile updated successfully for user '{request.user.username}'.")
                messages.success(request, 'Profile was changed')
                return redirect(reverse('user:profile'))
            else:
                logger.warning(f"Invalid profile update form data for user '{request.user.username}'. Errors: {profile_form.errors}")
                messages.error(request, 'There was an error updating your profile.')
        elif 'timezone_submit' in request.POST:
            timezone_form = UserTimezoneForm(request.POST, instance=request.user.timezone_info)
            logger.debug(f"Timezone update form submitted by user '{request.user.username}' with data: {request.POST}")
            if timezone_form.is_valid():
                timezone_form.save()
                logger.info(f"Timezone updated successfully for user '{request.user.username}' to '{request.user.timezone_info.timezone}'.")
                messages.success(request, 'Timezone updated')
                return redirect(reverse('user:profile'))
            else:
                logger.warning(f"Invalid timezone update form data for user '{request.user.username}'. Errors: {timezone_form.errors}")
                messages.error(request, 'There was an error updating your timezone.')
        elif 'note_submit' in request.POST:
            note_form = UserNoteForm(request.POST)
            logger.debug(f"Note creation form submitted by user '{request.user.username}' with data: {request.POST}")
            if note_form.is_valid():
                new_note = note_form.save(commit=False)
                new_note.user = request.user
                new_note.save()
                logger.info(f"Note created successfully for user '{request.user.username}': '{new_note.title}'.")
                messages.success(request, 'Note created')
                return redirect(reverse('user:profile'))
            else:
                logger.warning(f"Invalid note creation form data for user '{request.user.username}'. Errors: {note_form.errors}")
                messages.error(request, 'There was an error creating the note.')
        elif 'group_submit' in request.POST:
            group_form = UserGroupForm(request.POST)
            logger.debug(f"Group creation form submitted by user '{request.user.username}' with data: {request.POST}")
            if group_form.is_valid():
                new_group = group_form.save()
                new_group.members.add(request.user)
                logger.info(f"Group '{new_group.name}' created and user '{request.user.username}' added.")
                messages.success(request, 'Group created')
                return redirect(reverse('user:profile'))
            else:
                logger.warning(f"Invalid group creation form data for user '{request.user.username}'. Errors: {group_form.errors}")
                messages.error(request, 'There was an error creating the group.')

    orders = Order.objects.filter(user=request.user).prefetch_related(
        Prefetch(
            'items',
            queryset=OrderItem.objects.select_related('product'),
        )
    ).order_by('-id')
    logger.debug(f"Fetched {orders.count()} orders for user '{request.user.username}'.")

    notes = request.user.notes.all().order_by('-created_at')
    logger.debug(f"Fetched {notes.count()} notes for user '{request.user.username}'.")

    groups = request.user.user_groups.all().order_by('name')
    logger.debug(f"Fetched {groups.count()} groups for user '{request.user.username}'.")

    return render(request, 'users/profile.html',
                  {'form': profile_form,
                   'orders': orders,
                   'notes': notes,
                   'groups': groups,
                   'timezone_form': timezone_form,
                   'note_form': note_form,
                   'group_form': group_form})


def logout(request):
    username = request.user.username
    logger.info(f"User '{username}' logged out.")
    auth.logout(request)
    return redirect(reverse('main:product_list'))