from django.contrib.auth import forms as auth_forms
from django.contrib.auth.models import User
from django import forms
from django.http import Http404
from typing import Optional

from base.views_utils import ClassAuth, HerdAuth, auth_herd
from . import models
from .traitsets import TRAISET_CHOICES, Traitset


class UserCreationForm(auth_forms.UserCreationForm):
    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        ]


class CreateClassForm(forms.ModelForm):
    traitset = forms.ChoiceField(choices=TRAISET_CHOICES)

    class Meta:
        model = models.Class
        fields = ["name", "info", "traitset"]

    def save(self, user: User) -> models.Class:
        return models.Class.create_new(
            user,
            name=self.cleaned_data["name"],
            info=self.cleaned_data["info"],
            traitsetname=self.cleaned_data["traitset"],
        )


class UpdateClassForm(forms.ModelForm):
    name = forms.CharField(disabled=True)
    traitset = forms.CharField(disabled=True)
    classcode = forms.CharField(disabled=True)
    enrollment_tokens = forms.IntegerField(disabled=True)

    class Meta:
        model = models.Class
        fields = [
            "name",
            "traitset",
            "classcode",
            "enrollment_tokens",
            "info",
            "default_animal",
            "allow_other_animals",
        ]

    def __init__(self, *args, **kwargs):
        super(UpdateClassForm, self).__init__(*args, **kwargs)
        traitset = Traitset(self.instance.traitset)

        trait_visibility_choices = [
            (x.uid, f"{x.uid} ({x.user_key})") for x in traitset.traits
        ]

        recessive_visibility_choices = [
            (x.uid, f"{x.uid} ({x.user_key})") for x in traitset.recessives
        ]

        self.fields["genotype_visibility"] = forms.MultipleChoiceField(
            required=False,
            choices=trait_visibility_choices,
            widget=forms.CheckboxSelectMultiple(),
            initial=[
                x
                for x, _ in trait_visibility_choices
                if self.instance.trait_visibility[x][0]
            ],
        )
        self.fields["phenotype_visibility"] = forms.MultipleChoiceField(
            required=False,
            choices=trait_visibility_choices,
            widget=forms.CheckboxSelectMultiple(),
            initial=[
                x
                for x, _ in trait_visibility_choices
                if self.instance.trait_visibility[x][1]
            ],
        )
        self.fields["recessive_visibility"] = forms.MultipleChoiceField(
            required=False,
            choices=recessive_visibility_choices,
            widget=forms.CheckboxSelectMultiple(),
            initial=[
                x
                for x, _ in recessive_visibility_choices
                if self.instance.recessive_visibility[x]
            ],
        )

        self.fields["default_animal"] = forms.ChoiceField(
            choices=traitset.animal_choices
        )

    def save(self) -> None:
        self.instance.info = self.cleaned_data["info"]

        for trait in self.instance.trait_visibility:
            self.instance.trait_visibility[trait] = [
                trait in self.cleaned_data["genotype_visibility"],
                trait in self.cleaned_data["phenotype_visibility"],
            ]

        for recessive in self.instance.recessive_visibility:
            self.instance.recessive_visibility[recessive] = (
                recessive in self.cleaned_data["recessive_visibility"]
            )

        if self.instance.allow_other_animals is False:
            enrollments = models.Enrollment.objects.filter(connectedclass=self.instance)
            for enrollment in enrollments:
                enrollment.animal = self.instance.default_animal

            models.Enrollment.objects.bulk_update(enrollments, ["animal"])

        self.instance.save()


class ClassReadonlyForm(forms.ModelForm):
    name = forms.CharField(disabled=True)
    traitset = forms.CharField(disabled=True)
    info = forms.CharField(disabled=True, widget=forms.Textarea)

    class Meta:
        model = models.Class
        fields = ["name", "traitset", "info"]


class JoinClass(forms.Form):
    classcode = forms.CharField()

    def __init__(self, user: User = None, *args, **kwargs):
        self.user = user
        super(JoinClass, self).__init__(*args, **kwargs)

    def clean_classcode(self):
        try:
            connectedclass = models.Class.objects.get(
                classcode=self.cleaned_data["classcode"]
            )
        except models.Class.DoesNotExist:
            raise forms.ValidationError("No class with this code was found.")

        if models.Enrollment.objects.filter(
            connectedclass=connectedclass, student=self.user
        ).exists():
            raise forms.ValidationError("Already enrolled in class.")

        if models.EnrollmentRequest.objects.filter(
            connectedclass=connectedclass, student=self.user
        ).exists():
            raise forms.ValidationError("Already requested enrollment in class.")

        if connectedclass.teacher == self.user:
            raise forms.ValidationError("Cannot enroll in class as teacher.")

        return self.cleaned_data["classcode"]

    def save(self) -> models.EnrollmentRequest:
        connectedclass = models.Class.objects.get(
            classcode=self.cleaned_data["classcode"]
        )
        return models.EnrollmentRequest.create_new(self.user, connectedclass)


class BreedHerd(forms.Form):
    class ValidationCatch:
        males: list[models.Animal]
        assignment: models.Assignment
        assignment_fulfillment: models.AssignmentFulfillment
        assignment_step: models.AssignmentStep

    males = forms.JSONField(
        widget=forms.TextInput(attrs={"class": "full-width", "disabled": True}),
        label="",
        initial=list,
    )
    assignment = forms.IntegerField(widget=forms.HiddenInput)
    validation_catch: Optional[ValidationCatch] = None

    def validate_males(self, class_auth: ClassAuth.Student) -> bool:
        males = self.cleaned_data["males"]

        if type(males) != list:
            return False

        self.validation_catch.males = []
        for male in males:
            try:
                animal = models.Animal.objects.get(id=male)
                self.validation_catch.males.append(animal)
            except models.Animal.DoesNotExist:
                return False

            if not animal.male:
                return False

            try:
                herd_auth = auth_herd(class_auth, animal.herd_id)
            except Http404:
                return False

    def validate_assignment(self, class_auth: ClassAuth.Student) -> bool:
        assignment = self.cleaned_data["assignment"]

        try:
            assignment = models.Assignment.objects.get(id=assignment)
            self.validation_catch.assignment = assignment
        except models.Assignment.DoesNotExist:
            return False

        try:
            assignment_fulfillment = models.AssignmentFulfillment.objects.get(
                assignment=assignment, enrollment=class_auth.enrollment
            )
            self.validation_catch.assignment_fulfillment = assignment_fulfillment
        except models.AssignmentFulfillment.DoesNotExist:
            return False

        try:
            assignment_step = models.AssignmentStep.objects.get(
                assignment=assignment, number=assignment_fulfillment.current_step
            )
            self.validation_catch.assignment_step = assignment_step
        except models.AssignmentStep.DoesNotExist:
            return False

        return assignment_step.step == models.AssignmentStep.CHOICE_BREED

    def is_valid(self, class_auth: ClassAuth.Student) -> bool:
        self.validation_catch = self.ValidationCatch()

        if super().is_valid() is False:
            return False

        if self.validate_males(class_auth) is False:
            return False

        return self.validate_assignment(class_auth)

    def save(
        self, class_auth: ClassAuth.Student, herd_auth: HerdAuth.EnrollmentHerd
    ) -> None:
        herd_auth.herd.breed_herd(self.validation_catch.males)
        self.validation_catch.assignment_fulfillment.current_step += 1
        self.validation_catch.assignment_fulfillment.save()


class SubmitAnimal(forms.Form):
    class ValidationCatch:
        assignment: models.Assignment
        assignment_fulfillment: models.AssignmentFulfillment
        assignment_step: models.AssignmentStep

    assignment = forms.IntegerField(widget=forms.HiddenInput)
    validation_catch: Optional[ValidationCatch] = None

    def is_valid(self, class_auth: ClassAuth.Student) -> bool:
        self.validation_catch = self.ValidationCatch()

        if super().is_valid() is False:
            return False

        assignment = self.cleaned_data["assignment"]

        try:
            assignment = models.Assignment.objects.get(id=assignment)
            self.validation_catch.assignment = assignment
        except models.Assignment.DoesNotExist:
            return False

        try:
            assignment_fulfillment = models.AssignmentFulfillment.objects.get(
                assignment=assignment, enrollment=class_auth.enrollment
            )
            self.validation_catch.assignment_fulfillment = assignment_fulfillment
        except models.AssignmentFulfillment.DoesNotExist:
            return False

        try:
            assignment_step = models.AssignmentStep.objects.get(
                assignment=assignment, number=assignment_fulfillment.current_step
            )
            self.validation_catch.assignment_step = assignment_step
        except models.AssignmentStep.DoesNotExist:
            return False

        return assignment_step.step in [
            models.AssignmentStep.CHOICE_MALE_SUBMISSION,
            models.AssignmentStep.CHOICE_FEMALE_SUBMISSION,
        ]

    def save(self, class_auth: ClassAuth.Student, animal: models.Animal) -> None:
        animal.herd = class_auth.connectedclass.class_herd
        animal.save()

        self.validation_catch.assignment_fulfillment.current_step += 1
        self.validation_catch.assignment_fulfillment.save()


class NewAssignment(forms.ModelForm):
    startdate = forms.DateField()
    duedate = forms.DateField()

    class Meta:
        fields = ["name", "startdate", "duedate"]
        model = models.Assignment

    def is_valid(self) -> bool:
        return super().is_valid()
