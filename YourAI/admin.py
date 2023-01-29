from django.contrib import admin
from .models import *

# Register your models here.

class YourAIAdmin(admin.ModelAdmin):
    """Specialised admin view for the Customer model."""
    # set the fields to display
    def __init__(self, model, admin_site):
        self.list_display = [field.name for field in YourAIUser._meta.fields]
        super(YourAIAdmin, self).__init__(model, admin_site)


admin.site.register(YourAIUser,YourAIAdmin)