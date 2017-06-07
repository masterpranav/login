from django.contrib import admin
from accounts.models import UserProfile
from accounts.models import Clauses
# Register your models here.
admin.site.register(UserProfile)
admin.site.register(Clauses)