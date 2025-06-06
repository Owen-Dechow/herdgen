# base.models

## Class(Model)
Classroom object: manages class settings and enrollments.

### Fields
`name` django.db.models.fields.CharField

`teacher_id` django.db.models.fields.related.ForeignKey

`teacher` django.db.models.fields.related_descriptors.ForwardManyToOneDescriptor

`traitset` django.db.models.fields.CharField

`info` django.db.models.fields.TextField

`classcode` django.db.models.fields.CharField

`trait_visibility` django.db.models.fields.json.JSONField

`hide_female_pta` django.db.models.fields.BooleanField

`recessive_visibility` django.db.models.fields.json.JSONField

`net_merit_visibility` django.db.models.fields.BooleanField

`trend_log` django.db.models.fields.json.JSONField

`default_animal` django.db.models.fields.CharField

`allow_other_animals` django.db.models.fields.BooleanField

`quarantine_days` django.db.models.fields.IntegerField

`class_herd_id` django.db.models.fields.related.ForeignKey

`class_herd` django.db.models.fields.related_descriptors.ForwardManyToOneDescriptor

`enrollment_tokens` django.db.models.fields.IntegerField

### Methods
`generate_class_code() -> str` builtins.classmethod

Generates a UID for the class

`create_new(user: django.contrib.auth.models.User, name: str, traitsetname: str, info: str, initial_males: int, initial_females: int) -> 'Class'` builtins.classmethod

Create a new class

`decrement_enrollment_tokens(self)` builtins.function

Remove one enrollment token

`get_open_assignments(self) -> django.db.models.manager.BaseManager` builtins.function

Get a query of all open assignments

`update_trend_log(self, save: bool = True, new_animals: Optional[list['Animal']] = None, old_animals: Optional[list['Animal']] = None) -> None` builtins.function

Update the class trend log

`get_animal_file_headers(self) -> list[str]` builtins.function

Get file headers for animal csv file for class

`get_animal_file_data_order(self) -> list[str | tuple[str, str]]` builtins.function

Get animal file column ordering information

`recalculate_ptas(*args, **kwargs)` builtins.staticmethod

## Herd(Model)
Manages a group of animals

### Fields
`name` django.db.models.fields.CharField

`connectedclass_id` django.db.models.fields.related.ForeignKey

`connectedclass` django.db.models.fields.related_descriptors.ForwardManyToOneDescriptor

`breedings` django.db.models.fields.IntegerField

`enrollment_id` django.db.models.fields.related.ForeignKey

`enrollment` django.db.models.fields.related_descriptors.ForwardManyToOneDescriptor

### Methods
`generate_starter_herd(name: str, females: int, males: int, traitset: base.traitsets.traitset.Traitset, connectedclass: base.models.Class) -> 'Herd'` builtins.classmethod

Create a random herd for new enrollment

`generate_empty_herd(name: str, connectedclass: base.models.Class) -> 'Herd'` builtins.classmethod

Create a herd with no animals

`get_total_to_be_born(target_num_males: int, target_num_females: int, num_mothers: int) -> tuple[int, int, int]` builtins.classmethod

Calculate the number if male and females to be born to herd.
Based on target number and number of possible mothers

`breed_herd(self, sires: list['Animal']) -> base.models.Herd.BreedingResults` builtins.function

Run a breeding on herd

`json_dict(self) -> dict[str, typing.Any]` builtins.function

Get herd as json serializable dict

`collect_positive_fatal_recessive_animals(self, animals: list['Animal'], traitset: base.traitsets.traitset.Traitset) -> list['Animal']` builtins.function

Get a list of all animals with fatal genetic recessives

`collect_deaths_from_age(self, animals: list['Animal'], maxage: int) -> list['Animal']` builtins.function

Get a list of all animals that are too old

## Enrollment(Model)
Enrollment(id, student, connectedclass, animal, herd)

### Fields
`student_id` django.db.models.fields.related.ForeignKey

`student` django.db.models.fields.related_descriptors.ForwardManyToOneDescriptor

`connectedclass_id` django.db.models.fields.related.ForeignKey

`connectedclass` django.db.models.fields.related_descriptors.ForwardManyToOneDescriptor

`animal` django.db.models.fields.CharField

`herd_id` django.db.models.fields.related.ForeignKey

`herd` django.db.models.fields.related_descriptors.ForwardManyToOneDescriptor

### Methods
`create_from_enrollment_request(enrollment_request: 'EnrollmentRequest') -> 'Enrollment'` builtins.classmethod

`json_dict(self) -> dict[str, typing.Any]` builtins.function

`get_open_assignments_json_dict(self) -> dict[str, typing.Any]` builtins.function

## EnrollmentRequest(Model)
EnrollmentRequest(id, student, connectedclass)

### Fields
`student_id` django.db.models.fields.related.ForeignKey

`student` django.db.models.fields.related_descriptors.ForwardManyToOneDescriptor

`connectedclass_id` django.db.models.fields.related.ForeignKey

`connectedclass` django.db.models.fields.related_descriptors.ForwardManyToOneDescriptor

### Methods
`create_new(student: django.contrib.auth.models.User, connectedclass: 'Class') -> 'EnrollmentRequest'` builtins.classmethod

`json_dict(self) -> dict[str, typing.Any]` builtins.function

## Animal(Model)
Animal(id, herd, connectedclass, name, generation, male, genomic_tests, genotype, phenotype, ptas, recessives, sire, dam, pedigree, inbreeding, net_merit)

### Fields
`herd_id` django.db.models.fields.related.ForeignKey

`herd` django.db.models.fields.related_descriptors.ForwardManyToOneDescriptor

`connectedclass_id` django.db.models.fields.related.ForeignKey

`connectedclass` django.db.models.fields.related_descriptors.ForwardManyToOneDescriptor

`name` django.db.models.fields.CharField

`generation` django.db.models.fields.IntegerField

`male` django.db.models.fields.BooleanField

`genomic_tests` django.db.models.fields.IntegerField

`genotype` django.db.models.fields.json.JSONField

`phenotype` django.db.models.fields.json.JSONField

`ptas` django.db.models.fields.json.JSONField

`recessives` django.db.models.fields.json.JSONField

`sire_id` django.db.models.fields.related.ForeignKey

`sire` django.db.models.fields.related_descriptors.ForwardManyToOneDescriptor

`dam_id` django.db.models.fields.related.ForeignKey

`dam` django.db.models.fields.related_descriptors.ForwardManyToOneDescriptor

`pedigree` django.db.models.fields.json.JSONField

`inbreeding` django.db.models.fields.FloatField

`net_merit` django.db.models.fields.FloatField

### Methods
`generate_random_unsaved(male: bool, herd: base.models.Herd, traitset: base.traitsets.traitset.Traitset, connectedclass: base.models.Class) -> 'Animal'` builtins.classmethod

`generate_from_breeding_unsaved(male: bool, herd: base.models.Herd, traitset: base.traitsets.traitset.Traitset, connectedclass: base.models.Class, sire: 'Animal', dam: 'Animal') -> 'Animal'` builtins.classmethod

`finalize_animal_unsaved(self, herd: base.models.Herd) -> None` builtins.function

`resolve_data_key(self, data_key: str | tuple[str, str], connectedclass: Optional[base.models.Class] = None) -> Any` builtins.function

`json_dict(self) -> dict[str, typing.Any]` builtins.function

`recalculate_pta_unsaved(self, number_of_daughters: int, traitset: base.traitsets.traitset.Traitset)` builtins.function

## Assignment(Model)
Assignment(id, connectedclass, startdate, duedate, name)

### Fields
`connectedclass_id` django.db.models.fields.related.ForeignKey

`connectedclass` django.db.models.fields.related_descriptors.ForwardManyToOneDescriptor

`startdate` django.db.models.fields.DateTimeField

`duedate` django.db.models.fields.DateTimeField

`name` django.db.models.fields.CharField

### Methods
`create_new(name: str, startdate: datetime.datetime, duedate: datetime.datetime, steps: list[str], connectedclass: base.models.Class) -> 'Assignment'` builtins.classmethod

## AssignmentStep(Model)
AssignmentStep(id, assignment, step, number)

### Fields
`CHOICE_MALE_SUBMISSION` builtins.str

`CHOICE_FEMALE_SUBMISSION` builtins.str

`CHOICE_BREED` builtins.str

`CHOICES` builtins.tuple

`assignment_id` django.db.models.fields.related.ForeignKey

`assignment` django.db.models.fields.related_descriptors.ForwardManyToOneDescriptor

`step` django.db.models.fields.CharField

`get_step_display` functools.partialmethod

`number` django.db.models.fields.IntegerField

### Methods
`verbose_step(self) -> Optional[str]` builtins.function

## AssignmentFulfillment(Model)
AssignmentFulfillment(id, enrollment, assignment, current_step)

### Fields
`enrollment_id` django.db.models.fields.related.ForeignKey

`enrollment` django.db.models.fields.related_descriptors.ForwardManyToOneDescriptor

`assignment_id` django.db.models.fields.related.ForeignKey

`assignment` django.db.models.fields.related_descriptors.ForwardManyToOneDescriptor

`current_step` django.db.models.fields.IntegerField

### Methods
