from django.contrib.auth.models import User
from django.db import models
from .managers import YourAIUserManager


class YourAIUser(models.Model):
    id = models.AutoField(primary_key=True)
    token = models.CharField(max_length=10000,default="ABCD")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.CharField(max_length=100,unique=True)
    password = models.CharField(max_length=100,null=True)
    phone = models.CharField(max_length=100,null=True)
    registration_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    last_request_date = models.DateTimeField(null=True)
    coins = models.FloatField(default=20) # when someone register, he gets free 20 coins
    is_active = models.BooleanField(default=True) # when someone register, his account is inactive until he activate it via link

    def __str__(self):
        return self.email

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = YourAIUserManager()


# class to hold the payment transactions log
class TransactionLog(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.CharField(max_length=100)
    datetime = models.DateTimeField(auto_now_add=True)
    price = models.FloatField()
    status = models.CharField(max_length=100) # { pending / success }
    # pending : when customer arrive to checkout page
    # success: after coins are assigned

    def __str__(self):
        return str(self.id)
