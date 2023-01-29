#from django.contrib.auth.models import User
from django.contrib.auth.models import User

from .models import YourAIUser


class EmailAuthBackend:
    """
    Custom authentication backend.

    Allows users to log in using their email address.
    """

    def authenticate(self, request, username=None, password=None):
        try:
            # i use both User and YourAIUser
            # i extract userAI and user because they have same email, i check if the entered password matches userAI's
            # if so i return the User object
            user = User.objects.get(email=username)
            userAI = YourAIUser.objects.get(email=username)

            if userAI.password == password:
                return user
                # check if the expiry date hasnt come yet
            return None
        except:
            return None

    def get_user(self, user_id):
        """
        Overrides the get_user method to allow users to log in using their email address.
        """
        try:
            return User.objects.get(pk=user_id)
        except:
            return None