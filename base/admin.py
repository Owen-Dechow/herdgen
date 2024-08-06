from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.Class)
admin.site.register(models.Herd)
admin.site.register(models.Enrollment)
admin.site.register(models.Animal)
admin.site.register(models.Assignment)
admin.site.register(models.AssignmentStep)
admin.site.register(models.AssignmentFulfillment)
