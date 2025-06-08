# base.forms
## EmailAuthenticationForm
> None

### Bases
* django.contrib.auth.forms.AuthenticationForm

### Fields
### Methods
### Source
```python
class EmailAuthenticationForm(auth_forms.AuthenticationForm):
    username = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={"autofocus": True}),
    )

    def clean(self):
        ERROR_MSG = forms.ValidationError(
            "Please enter a correct username and email. Note that both fields may be case-sensitive."
        )

        email = self.cleaned_data.get("username")
        user = User.objects.filter(email=email).order_by("id").last()
        if user:
            self.user_cache = authenticate(
                self.request,
                username=user.username,
                password=self.cleaned_data.get("password"),
            )
            if self.user_cache is None:
                raise ERROR_MSG
        else:
            raise ERROR_MSG

        return self.cleaned_data

```

## UserCreationForm
> None

### Bases
* django.contrib.auth.forms.UserCreationForm

### Fields
### Methods
`clean_email(self) -> str` builtins.function

### Source
```python
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

    def clean_email(self) -> str:
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).count() > 0:
            raise forms.ValidationError("A user with that email already exists.")

        return email

```

## CreateClassForm
> None

### Bases
* django.forms.models.ModelForm

### Fields
`_meta` django.forms.models.ModelFormOptions

### Methods
`clean_name(self)` builtins.function

`save(self, user: django.contrib.auth.models.User) -> base.models.Class` builtins.function

### Source
```python
class CreateClassForm(forms.ModelForm):
    traitset = forms.ChoiceField(choices=TRAITSET_CHOICES)
    initial_males = forms.IntegerField(min_value=1, max_value=100)
    initial_females = forms.IntegerField(min_value=1, max_value=25)

    class Meta:
        model = models.Class
        fields = ["name", "info", "traitset"]

    def clean_name(self):
        name = self.data["name"]
        error = forms.ValidationError("Name cannot contain < or >")
        if "<" in name or ">" in name:
            raise error

        return name

    def save(self, user: User) -> models.Class:
        return models.Class.create_new(
            user,
            name=self.cleaned_data["name"],
            info=self.cleaned_data["info"],
            traitsetname=self.cleaned_data["traitset"],
            initial_males=self.cleaned_data["initial_males"],
            initial_females=self.cleaned_data["initial_females"],
        )

```

## UpdateClassForm
> None

### Bases
* django.forms.models.ModelForm

### Fields
`_meta` django.forms.models.ModelFormOptions

### Methods
`clean_name(self)` builtins.function

`__init__(self, connectedclass: base.models.Class, *args, **kwargs)` builtins.function

`save(self) -> None` builtins.function

### Source
```python
class UpdateClassForm(forms.ModelForm):
    traitset = forms.CharField(disabled=True)
    classcode = forms.CharField(disabled=True)
    enrollment_tokens = forms.IntegerField(disabled=True)
    quarantine_days = forms.IntegerField(min_value=0, max_value=60)

    class Meta:
        model = models.Class
        fields = [
            "name",
            "traitset",
            "classcode",
            "enrollment_tokens",
            "info",
            "default_animal",
            "quarantine_days",
            "allow_other_animals",
            "net_merit_visibility",
            "hide_female_pta",
        ]

    def clean_name(self):
        name = self.data["name"]
        error = forms.ValidationError("Name cannot contain < or >")
        if "<" in name or ">" in name:
            raise error

        return name

    def __init__(self, connectedclass: models.Class, *args, **kwargs):
        super(UpdateClassForm, self).__init__(*args, **kwargs)
        traitset = Traitset(self.instance.traitset)

        trait_visibility_choices = [
            (x.uid, filter_text_to_default(f"<{x.uid}>", connectedclass))
            for x in traitset.traits
        ]

        recessive_visibility_choices = [
            (x.uid, filter_text_to_default(f"<{x.uid}>", connectedclass))
            for x in traitset.recessives
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

        self.fields["pta_visibility"] = forms.MultipleChoiceField(
            required=False,
            choices=trait_visibility_choices,
            widget=forms.CheckboxSelectMultiple(),
            initial=[
                x
                for x, _ in trait_visibility_choices
                if self.instance.trait_visibility[x][2]
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
                trait in self.cleaned_data["pta_visibility"],
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

```

## ClassReadonlyForm
> None

### Bases
* django.forms.models.ModelForm

### Fields
`_meta` django.forms.models.ModelFormOptions

### Methods
### Source
```python
class ClassReadonlyForm(forms.ModelForm):
    name = forms.CharField(disabled=True)
    traitset = forms.CharField(disabled=True)
    info = forms.CharField(disabled=True, widget=forms.Textarea)

    class Meta:
        model = models.Class
        fields = ["name", "traitset", "info"]

```

## JoinClass
> None

### Bases
* django.forms.forms.Form

### Fields
### Methods
`__init__(self, user: django.contrib.auth.models.User = None, *args, **kwargs)` builtins.function

`clean_classcode(self)` builtins.function

`save(self) -> base.models.EnrollmentRequest` builtins.function

### Source
```python
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

```

## BreedHerd
> None

### Bases
* django.forms.forms.Form

### Fields
`__annotations__` builtins.dict

`validation_catch` builtins.NoneType

### Methods
`validate_males(self, class_auth: base.views_utils.ClassAuth.Student) -> bool` builtins.function

`validate_assignment(self, class_auth: base.views_utils.ClassAuth.Student) -> bool` builtins.function

`is_valid(self, class_auth: base.views_utils.ClassAuth.Student) -> bool` builtins.function

`save(self, herd_auth: base.views_utils.HerdAuth.EnrollmentHerd) -> base.models.Herd.BreedingResults` builtins.function

### Source
```python
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

        return True

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

    def save(self, herd_auth: HerdAuth.EnrollmentHerd) -> models.Herd.BreedingResults:
        breeding_result = herd_auth.herd.breed_herd(self.validation_catch.males)
        self.validation_catch.assignment_fulfillment.current_step += 1
        self.validation_catch.assignment_fulfillment.save()
        return breeding_result

```

## SubmitAnimal
> None

### Bases
* django.forms.forms.Form

### Fields
`__annotations__` builtins.dict

`validation_catch` builtins.NoneType

### Methods
`is_valid(self, class_auth: base.views_utils.ClassAuth.Student) -> bool` builtins.function

`move_animal(*args, **kwargs)` background_task.tasks.TaskProxy

`save(self, class_auth: base.views_utils.ClassAuth.Student, animal: base.models.Animal) -> None` builtins.function

### Source
```python
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

    @background_task.background(schedule=0)
    @staticmethod
    def move_animal(animal_id: int):
        animal = (
            models.Animal.objects.select_related("connectedclass")
            .defer("pedigree", "connectedclass__trend_log")
            .get(id=animal_id)
        )
        animal.herd = animal.connectedclass.class_herd
        animal.save()

    def save(self, class_auth: ClassAuth.Student, animal: models.Animal) -> None:
        animal.herd = None
        animal.save()

        day = 60 * 60 * 24
        self.move_animal(
            animal_id=animal.id,
            schedule=class_auth.connectedclass.quarantine_days * day,
        )

        self.validation_catch.assignment_fulfillment.current_step += 1
        self.validation_catch.assignment_fulfillment.save()

```

## NewAssignment
> None

### Bases
* django.forms.models.ModelForm

### Fields
`_meta` django.forms.models.ModelFormOptions

### Methods
`clean_steps(self) -> list[str]` builtins.function

`clean_name(self)` builtins.function

`save(self, connectedclass: base.models.Class) -> base.models.Assignment` builtins.function

### Source
```python
class NewAssignment(forms.ModelForm):
    startdate = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )
    duedate = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )
    steps = forms.JSONField(widget=forms.HiddenInput, required=False)

    class Meta:
        fields = ["name", "startdate", "duedate"]
        model = models.Assignment

    def clean_steps(self) -> list[str]:
        steps = self.cleaned_data["steps"]
        possible_steps = [x[0] for x in models.AssignmentStep.CHOICES]

        if type(steps) is not list:
            raise forms.ValidationError("Invalid steps")

        for step in steps:
            if step not in possible_steps:
                raise forms.ValidationError("Invalid step")

        return steps

    def clean_name(self):
        name = self.data["name"]
        error = forms.ValidationError("Name cannot contain < or >")
        if "<" in name or ">" in name:
            raise error

        return name

    def save(self, connectedclass: models.Class) -> models.Assignment:
        return models.Assignment.create_new(
            self.cleaned_data["name"],
            self.cleaned_data["startdate"],
            self.cleaned_data["duedate"],
            self.cleaned_data["steps"],
            connectedclass,
        )

```

## UpdateAssignment
> None

### Bases
* django.forms.models.ModelForm

### Fields
`_meta` django.forms.models.ModelFormOptions

### Methods
`__init__(self, *args, **kwargs)` builtins.function

### Source
```python
class UpdateAssignment(forms.ModelForm):
    startdate = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )
    duedate = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )
    steps = forms.JSONField(disabled=True, widget=forms.TextInput, required=False)

    def __init__(self, *args, **kwargs):
        super(UpdateAssignment, self).__init__(*args, **kwargs)

        self.fields["steps"].initial = [
            x.step
            for x in models.AssignmentStep.objects.filter(assignment=self.instance)
        ]

    class Meta:
        fields = ["name", "startdate", "duedate"]
        model = models.Assignment

```

## UpdateEnrollmentForm
> None

### Bases
* django.forms.models.ModelForm

### Fields
`_meta` django.forms.models.ModelFormOptions

### Methods
`__init__(self, *args, **kwargs)` builtins.function

### Source
```python
class UpdateEnrollmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UpdateEnrollmentForm, self).__init__(*args, **kwargs)

        if self.instance.connectedclass.allow_other_animals:
            self.fields["animal"] = forms.ChoiceField(
                label="Animal Filter",
                choices=Traitset(self.instance.connectedclass.traitset).animal_choices,
            )
        else:
            self.fields["animal"] = forms.ChoiceField(
                label="Animal Filter",
                choices=Traitset(self.instance.connectedclass.traitset).animal_choices,
                disabled=True,
            )

    class Meta:
        model = models.Enrollment
        fields = ["animal"]

```

## Account
> None

### Bases
* django.forms.models.ModelForm

### Fields
`_meta` django.forms.models.ModelFormOptions

### Methods
### Source
```python
class Account(forms.ModelForm):
    username = forms.CharField(disabled=True)
    email = forms.EmailField(disabled=True)
    first_name = forms.CharField(disabled=True)
    last_name = forms.CharField(disabled=True)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]

```

## DeleteAccount
> None

### Bases
* django.forms.forms.Form

### Fields
### Methods
`is_valid(self, user: django.contrib.auth.models.User) -> bool` builtins.function

`clean_password(self) -> str` builtins.function

### Source
```python
class DeleteAccount(forms.Form):
    password = forms.CharField(strip=False, widget=forms.PasswordInput)

    def is_valid(self, user: User) -> bool:
        self.user = user
        return super().is_valid()

    def clean_password(self) -> str:
        password = self.cleaned_data["password"]
        if not self.user.check_password(password):
            raise forms.ValidationError(
                "Password was incorrect.",
                code="password_incorrect",
            )
        return password

```

