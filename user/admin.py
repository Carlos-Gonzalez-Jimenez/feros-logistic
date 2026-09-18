from django.contrib import admin
from user.models import User, EventLog
from django.contrib.auth.models import Permission

admin.site.register(User)
admin.site.register(Permission)
admin.site.register(EventLog)
