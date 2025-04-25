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


class Task(models.Model):
    
    STATUS_CHOICES = [
        ("PENDING" , "Pending"),
        ("COMPLETED", "Completed"),
        ("EXPIRED", "Expired")
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=80, null=False)
    description = models.TextField()
    status = models.CharField(choices=STATUS_CHOICES, default='PENDING', null=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    due_date = models.DateTimeField(null=False)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
    @property
    def current_status(self):
        if self.status != 'COMPLETED' and timezone.now() > self.due_date:
            self.status = 'EXPIRED'
            self.save(update_fields=['status'])
        return self.status
     