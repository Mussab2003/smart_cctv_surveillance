from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from uuid import uuid4
from django.utils import timezone
from .managers import UserManager

class User(AbstractBaseUser):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    username = models.CharField(max_length=50, null=False)
    email = models.EmailField(null=False, unique=True)
    password = models.CharField()
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    is_staff = models.BooleanField(default=False)

    def __str__(self):
        return self.username

    USERNAME_FIELD = 'email'
    objects = UserManager()

class Vehicle(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles')
    name = models.CharField(max_length=100)
    registration_number = models.CharField(max_length=50, blank=True, null=True)
    reference_image = models.URLField(null=True)

class DetectionEvent(models.Model):
    EVENT_TYPES = [
        ('CAR_MOVEMENT', 'Car Movement'),
        ('ENVIRONMENTAL_HAZARD', 'Fire or Smoke'),
        ('UNAUTHORIZED_ACCESS', 'Unauthorized Access')
    ]

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    video_frame = models.URLField(null=True)
    description = models.TextField(blank=True, null=True)
    is_alert_sent = models.BooleanField(default=False)

     