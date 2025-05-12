import pytz

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    image = models.ImageField(upload_to='users_image', blank=True,
                                 null=True)

    class Meta:
        db_table = 'user'

    def __str__(self):
        return self.username

class UserNote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes')
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class UserGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    members = models.ManyToManyField(User, related_name='user_groups')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class UserTimezone(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='timezone_info')
    timezone = models.CharField(
        max_length=50,
        default='Europe/Minsk',
        choices=[(tz, tz) for tz in pytz.all_timezones]
    )

    def __str__(self):
        return f'{self.user.username}\'s Timezone'