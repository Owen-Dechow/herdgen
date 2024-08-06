from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Class(models.Model):
    name = models.CharField(max_length=255)
    teacher = models.ForeignKey(to=User, on_delete=models.CASCADE)
    traitset = models.CharField(max_length=255)
    info = models.TextField(blank=True, null=True)
    classcode = models.CharField(max_length=255)
    trait_visibility = models.JSONField()
    recessive_visibility = models.JSONField()
    trend_log = models.JSONField(default=dict)
    starter_herd = models.ForeignKey(
        to="Herd",
        on_delete=models.CASCADE,
        related_name="class_starter_herd",
    )
    class_herd = models.ForeignKey(
        to="Herd",
        on_delete=models.CASCADE,
        related_name="class_class_herd",
    )
    enrollment_tokens = models.IntegerField(default=0)


class Herd(models.Model):
    name = models.CharField(max_length=255)
    connected_class = models.ForeignKey(to="Class", on_delete=models.CASCADE)
    breedings = models.IntegerField(default=0)
    enrollment = models.ForeignKey(
        to="Enrollment",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="herd_enrollment",
    )


class Enrollment(models.Model):
    student = models.ForeignKey(to=User, on_delete=models.CASCADE)
    connectedclass = models.ForeignKey(to="Class", on_delete=models.CASCADE)
    herd = models.ForeignKey(
        to="Herd", on_delete=models.CASCADE, related_name="enrollment_herd"
    )


class Animal(models.Model):
    herd = models.ForeignKey(to="Herd", on_delete=models.SET_NULL, null=True)
    connectedclass = models.ForeignKey(to="Class", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    generation = models.IntegerField(default=0)
    male = models.BooleanField()

    genotype = models.JSONField(default=dict)
    phenotype = models.JSONField(default=dict)
    recessives = models.JSONField(default=dict)

    sire = models.ForeignKey(
        to="Animal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="animal_sire",
    )
    dam = models.ForeignKey(
        to="Animal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="animal_dam",
    )

    pedigree = models.JSONField(null=True, blank=True)
    inbreeding = models.FloatField(null=True, blank=True)


class Assignment(models.Model):
    startdate = models.DateTimeField(null=True, blank=True)
    duedate = models.DateTimeField(null=True, blank=True)


class AssignmentStep(models.Model):
    CHOICES = (
        ("msub", "Submit Bull"),
        ("fsub", "Submit Cow"),
        ("breed", "Breed"),
    )

    step = models.CharField(choices=CHOICES, max_length=255)
    number = models.IntegerField()


class AssignmentFulfillment(models.Model):
    enrollment = models.ForeignKey(to="Enrollment", on_delete=models.CASCADE)
    assignment = models.ForeignKey(to="Assignment", on_delete=models.CASCADE)
    current_step = models.IntegerField(default=0)
