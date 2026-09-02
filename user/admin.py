from django.contrib import admin
from user.models import User, EventLog, Fee, Organization
from django.contrib.auth.models import Permission

admin.site.register(User)
admin.site.register(Organization)
admin.site.register(Permission)
admin.site.register(EventLog)
admin.site.register(Fee)
