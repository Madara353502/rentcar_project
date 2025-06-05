from django.contrib.auth.models import AbstractUser
from django.db import models
import pytz

TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.all_timezones]

class User(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    timezone = models.CharField(max_length=50, choices=TIMEZONE_CHOICES, default='UTC')
    
    def __str__(self):
        return self.username 