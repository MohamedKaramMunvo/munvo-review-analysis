from django.contrib.auth.models import User
from YourAI.models import YourAIUser


# get user (YourAIUser) using the (User) email
def getUser(email):
    user = YourAIUser.objects.get(email=email)
    return user