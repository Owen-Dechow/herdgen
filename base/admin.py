from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.Class, models.Class.Admin)
admin.site.register(models.Herd, models.Herd.Admin)
admin.site.register(models.Enrollment, models.Enrollment.Admin)
admin.site.register(models.EnrollmentRequest, models.EnrollmentRequest.Admin)
admin.site.register(models.Animal, models.Animal.Admin)
admin.site.register(models.Assignment, models.Assignment.Admin)
admin.site.register(models.AssignmentStep, models.AssignmentStep.Admin)
admin.site.register(models.AssignmentFulfillment, models.AssignmentFulfillment.Admin)
