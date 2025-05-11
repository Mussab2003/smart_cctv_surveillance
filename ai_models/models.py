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

class FacialEmbedding(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='embeddings')
    embedding_vector = models.JSONField()  # Storing the 512D embedding as a JSON array of floats
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self):
        return f"Embedding for {self.user.username} at {self.created_at}"


class Vehicle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles')
    vehicle_name = models.CharField(max_length=100)
    registration_number = models.CharField(max_length=50, blank=True, null=True)
    reference_image = models.URLField(null=True)
    vehicle_location_x = models.FloatField(null=True, blank=True)
    vehicle_location_y = models.FloatField(null=True, blank=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['owner', 'vehicle_name'], name='unique_vehicle_name_per_owner')
        ]
    
    def __str__(self):
        return f"{self.vehicle_name} - {self.owner.username}"
    
class DetectionEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    EVENT_TYPES = [
        ('CAR_MOVEMENT', 'Car Movement'),
        ('ENVIRONMENTAL_HAZARD', 'Fire or Smoke'),
        ('UNAUTHORIZED_ACCESS', 'Unauthorized Access')
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='events', null=True)
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    video_frame = models.URLField(null=True)
    description = models.TextField(blank=True, null=True)
    is_alert_sent = models.BooleanField(default=False)

class Video(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    VIDEO_TYPE_CHOICES = [
        ('upload', 'Uploaded Video'),
        ('stream', 'Live Stream'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='videos')
    video_type = models.CharField(max_length=10, choices=VIDEO_TYPE_CHOICES)
    video_url = models.URLField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)
    processing_result = models.JSONField(null=True, blank=True)  # optional: detection/tracking results

    def __str__(self):
        return f"{self.video_type} by {self.owner} at {self.uploaded_at}"
    
    