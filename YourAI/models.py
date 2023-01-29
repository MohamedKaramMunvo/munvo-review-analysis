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
    registration_date = models.DateTimeField()
    last_request_date = models.DateTimeField(null=True)
    expiry_date = models.DateTimeField(null=True)
    pack = models.CharField(max_length=100,null=True)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True)
    is_authenticated = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    def __str__(self):
        return self.email

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = YourAIUserManager()


# customized authentication backend
'''
class AuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None,expiry_date=None):
        # Check the username/password and return a user.
        login_valid = (settings.ADMIN_LOGIN == username)
        pwd_valid = check_password(password, settings.ADMIN_PASSWORD)
        # Check if user expiry date has not arrived yet
        if login_valid and pwd_valid:
            try:
                user = User.objects.get(username=username)
                # Check if user expiry date has not arrived yet
                if expiry_date <= user.expiry_date :
                    return None
            except User.DoesNotExist:
                # Create a new user. There's no need to set a password
                # because only the password from settings.py is checked.
                user = User(username=username)
                user.is_staff = True
                user.is_superuser = False
                user.save()
            return user
        return None
'''