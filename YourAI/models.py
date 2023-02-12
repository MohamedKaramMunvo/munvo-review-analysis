from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.backends import BaseBackend
from .managers import YourAIUserManager


class YourAIUser(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.CharField(max_length=100,unique=True)
    password = models.CharField(max_length=100,null=True)
    phone = models.CharField(max_length=100,null=True)
    registration_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    last_request_date = models.DateTimeField(null=True)
    expiry_date = models.DateTimeField(auto_now_add=True, null=True, blank=True) # the date when the pack will expire
    pack = models.CharField(max_length=100,null=True) # the pack choose FREE,PRO (later : BASIC,STANDARD,PREMIUM)
    api_count = models.IntegerField(default=20) # the api tries allowed for a free account
    is_active = models.BooleanField(default=True) # when someone register, his account is inactive until he activate it via link

    def __str__(self):
        return self.email

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = YourAIUserManager()

