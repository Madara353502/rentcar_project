import pytz
from django.utils import timezone
from cars.models import UserSession

class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            tzname = request.user.timezone
        else:
            tzname = request.session.get('django_timezone')
        
        if tzname:
            timezone.activate(pytz.timezone(tzname))
        else:
            timezone.deactivate()
        return self.get_response(request)

class SessionTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Start new session if none exists
            if not request.session.get('current_session_id'):
                session = UserSession.objects.create(user=request.user)
                request.session['current_session_id'] = session.id
            
        response = self.get_response(request)

        return response

    def process_request(self, request):
        if request.user.is_authenticated and request.session.get('current_session_id'):
            try:
                session = UserSession.objects.get(id=request.session['current_session_id'])
                # Update last activity
                session.end_time = timezone.now()
                session.duration = session.end_time - session.start_time
                session.save()
            except UserSession.DoesNotExist:
                # Session record was deleted, create new one
                session = UserSession.objects.create(user=request.user)
                request.session['current_session_id'] = session.id 