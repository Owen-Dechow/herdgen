# base.models
## Class(Model)
> Classroom object: manages class settings and enrollments.

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

> Generates a UID for the class

<details>
<summary>View Source</summary>
```python
@classmethod
def generate_class_code(cls) -> str:
    """Generates a UID for the class"""

    CHARACTERS = (
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
    )
    SECTIONS = 3
    SECTION_LENGTH = 3
    return "-".join(
        [
            "".join([choice(CHARACTERS) for _ in range(SECTION_LENGTH)])
            for _ in range(SECTIONS)
        ]
    )

```
<details>

`create_new(user: django.contrib.auth.models.User, name: str, traitsetname: str, info: str, initial_males: int, initial_females: int) -> 'Class'` builtins.classmethod

> Create a new class

<details>
<summary>View Source</summary>
```python
@classmethod
def create_new(
    cls,
    user: User,
    name: str,
    traitsetname: str,
    info: str,
    initial_males: int,
    initial_females: int,
) -> "Class":
    """Create a new class"""

    new = cls(name=name, traitset=traitsetname, info=info, teacher=user)
    new.classcode = cls.generate_class_code()

    traitset = Traitset(traitsetname)
    new.trait_visibility = traitset.get_default_trait_visibility()
    new.recessive_visibility = traitset.get_default_recessive_visibility()
    new.default_animal = traitset.animal_choices[0][0]
    new.save()

    new.class_herd = Herd.generate_starter_herd(
        name=f"{name} class <herd>",
        females=initial_females,
        males=initial_males,
        traitset=traitset,
        connectedclass=new,
    )

    new.update_trend_log(save=False)

    new.save()

    return new

```
<details>

`decrement_enrollment_tokens(self)` builtins.function

> Remove one enrollment token

<details>
<summary>View Source</summary>
```python
def decrement_enrollment_tokens(self):
    """Remove one enrollment token"""

    self.enrollment_tokens -= 1
    self.save()

```
<details>

`get_open_assignments(self) -> django.db.models.manager.BaseManager` builtins.function

> Get a query of all open assignments

<details>
<summary>View Source</summary>
```python
def get_open_assignments(self) -> models.manager.BaseManager["Assignment"]:
    """Get a query of all open assignments"""

    return Assignment.objects.filter(
        connectedclass=self, startdate__lte=now(), duedate__gte=now()
    )

```
<details>

`update_trend_log(self, save: bool = True, new_animals: Optional[list['Animal']] = None, old_animals: Optional[list['Animal']] = None) -> None` builtins.function

> Update the class trend log

<details>
<summary>View Source</summary>
```python
def update_trend_log(
    self,
    save: bool = True,
    new_animals: Optional[list["Animal"]] = None,
    old_animals: Optional[list["Animal"]] = None,
) -> None:
    """Update the class trend log"""

    if new_animals is not None and old_animals is not None:
        last = self.trend_log[-1]
        last_pop = last[nms.POPULATION_SIZE_KEY]
        new_pop = last_pop - len(old_animals) + len(new_animals)

        capture = {
            nms.GENOTYPE_KEY: {},
            nms.PHENOTYPE_KEY: {},
            nms.PTA_KEY: {},
        }
        for key, val in last[nms.GENOTYPE_KEY].items():
            old_sum = 0
            for animal in old_animals:
                old_sum += animal.genotype[key]

            new_sum = 0
            for animal in new_animals:
                new_sum += animal.genotype[key]

            capture[nms.GENOTYPE_KEY][key] = (
                (val * last_pop) - old_sum + new_sum
            ) / new_pop

        for key, val in last[nms.PHENOTYPE_KEY].items():
            old_sum = 0
            for animal in old_animals:
                old_sum += animal.phenotype[key] or 0

            new_sum = 0
            for animal in new_animals:
                new_sum += animal.phenotype[key] or 0

            capture[nms.PHENOTYPE_KEY][key] = (
                (val * last_pop) - old_sum + new_sum
            ) / new_pop

        if nms.PTA_KEY in last:
            for key, val in last[nms.PTA_KEY].items():
                old_sum = 0
                for animal in old_animals:
                    old_sum += animal.ptas[key]

                new_sum = 0
                for animal in new_animals:
                    new_sum += animal.ptas[key]

                capture[nms.PTA_KEY][key] = (
                    (val * last_pop) - old_sum + new_sum
                ) / new_pop

        old_nm = 0
        for animal in old_animals:
            old_nm += animal.net_merit

        new_nm = 0
        for animal in new_animals:
            new_nm += animal.net_merit

        last_nm = last[nms.NETMERIT_KEY]
        capture[nms.NETMERIT_KEY] = (
            (last_nm * last_pop) - old_nm + new_nm
        ) / new_pop
        capture[nms.POPULATION_SIZE_KEY] = new_pop

        capture[nms.TIME_STAMP_KEY] = now().isoformat()
    else:
        capture = {
            nms.GENOTYPE_KEY: defaultdict(int),
            nms.PHENOTYPE_KEY: defaultdict(int),
            nms.PTA_KEY: defaultdict(int),
        }
        net_merit_capture = 0

        animals = Animal.objects.defer("pedigree").filter(
            connectedclass=self
        )
        num_animals_alive = 0
        for animal in animals:
            if animal.herd_id is None:
                continue
            else:
                num_animals_alive += 1

            net_merit_capture += animal.net_merit

            for key, val in animal.genotype.items():
                capture[nms.GENOTYPE_KEY][key] += val

            for key, val in animal.phenotype.items():
                capture[nms.PHENOTYPE_KEY][key] += val or 0

            for key, val in animal.ptas.items():
                capture[nms.PTA_KEY][key] += val

        net_merit_capture = net_merit_capture / num_animals_alive

        for key, val in capture[nms.GENOTYPE_KEY].items():
            capture[nms.GENOTYPE_KEY][key] = val / num_animals_alive

        for key, val in capture[nms.PHENOTYPE_KEY].items():
            capture[nms.PHENOTYPE_KEY][key] = val / num_animals_alive

        for key, val in capture[nms.PTA_KEY].items():
            capture[nms.PTA_KEY][key] = val / num_animals_alive

        capture[nms.TIME_STAMP_KEY] = now().isoformat()
        capture[nms.POPULATION_SIZE_KEY] = num_animals_alive
        capture[nms.NETMERIT_KEY] = net_merit_capture

    self.trend_log.append(capture)

    if save:
        self.save()

```
<details>

`get_animal_file_headers(self) -> list[str]` builtins.function

> Get file headers for animal csv file for class

<details>
<summary>View Source</summary>
```python
def get_animal_file_headers(self) -> list[str]:
    """Get file headers for animal csv file for class"""

    traitset = Traitset(self.traitset)

    return (
        [
            "Id",
            "Name",
            "Herd",
            "Class",
            "Generation",
            "Sex",
            "Sire",
            "Dam",
            "Inbreeding Percent",
            "Net Merit $",
        ]
        + [
            filter_text_to_default(f"gen: <{x.uid}>", self)
            for x in traitset.traits
        ]
        + [
            filter_text_to_default(f"ph: <{x.uid}>", self)
            for x in traitset.traits
        ]
        + [
            filter_text_to_default(f"pta: <{x.uid}>", self)
            for x in traitset.traits
        ]
        + [
            filter_text_to_default(f"<{x.uid}>", self)
            for x in traitset.recessives
        ]
    )

```
<details>

`get_animal_file_data_order(self) -> list[str | tuple[str, str]]` builtins.function

> Get animal file column ordering information

<details>
<summary>View Source</summary>
```python
def get_animal_file_data_order(
    self,
) -> list[str | tuple[str, str]]:
    """Get animal file column ordering information"""
    traitset = Traitset(self.traitset)
    return (
        [
            nms.ID_KEY,
            nms.NAME_KEY,
            nms.HERD_NAME_KEY,
            nms.CLASS_NAME_KEY,
            nms.GENERATION_KEY,
            nms.SEX_KEY,
            nms.SIRE_ID_KEY,
            nms.DAM_ID_KEY,
            nms.INBREEDING_PERCENTAGE_KEY,
            nms.NETMERIT_KEY,
        ]
        + [(nms.GENOTYPE_KEY, x.uid) for x in traitset.traits]
        + [(nms.PHENOTYPE_KEY, x.uid) for x in traitset.traits]
        + [(nms.PTA_KEY, x.uid) for x in traitset.traits]
        + [
            (nms.FORMATTED_RECESSIVES_KEY, x.uid)
            for x in traitset.recessives
        ]
    )

```
<details>

`recalculate_ptas(*args, **kwargs)` builtins.staticmethod

## Herd(Model)
> Manages a group of animals

### Fields
`name` django.db.models.fields.CharField

`connectedclass_id` django.db.models.fields.related.ForeignKey

`connectedclass` django.db.models.fields.related_descriptors.ForwardManyToOneDescriptor

`breedings` django.db.models.fields.IntegerField

`enrollment_id` django.db.models.fields.related.ForeignKey

`enrollment` django.db.models.fields.related_descriptors.ForwardManyToOneDescriptor

### Methods
`generate_starter_herd(name: str, females: int, males: int, traitset: base.traitsets.traitset.Traitset, connectedclass: base.models.Class) -> 'Herd'` builtins.classmethod

> Create a random herd for new enrollment

<details>
<summary>View Source</summary>
```python
@classmethod
def generate_starter_herd(
    cls,
    name: str,
    females: int,
    males: int,
    traitset: Traitset,
    connectedclass: Class,
) -> "Herd":
    "Create a random herd for new enrollment"

    new = cls(name=name, connectedclass=connectedclass)
    new.save()

    male_animals = [
        Animal.generate_random_unsaved(True, new, traitset, connectedclass)
        for _ in range(males)
    ]

    female_animals = [
        Animal.generate_random_unsaved(
            False, new, traitset, connectedclass
        )
        for _ in range(females)
    ]

    Animal.objects.bulk_create(male_animals + female_animals)
    for animal in male_animals + female_animals:
        animal.finalize_animal_unsaved(new)
    Animal.objects.bulk_update(
        male_animals + female_animals, ["name", "pedigree", "inbreeding"]
    )

    return new

```
<details>

`generate_empty_herd(name: str, connectedclass: base.models.Class) -> 'Herd'` builtins.classmethod

> Create a herd with no animals

<details>
<summary>View Source</summary>
```python
@classmethod
def generate_empty_herd(cls, name: str, connectedclass: Class) -> "Herd":
    "Create a herd with no animals"

    new = cls(name=name, connectedclass=connectedclass)
    new.save()

    return new

```
<details>

`get_total_to_be_born(target_num_males: int, target_num_females: int, num_mothers: int) -> tuple[int, int, int]` builtins.classmethod

> Calculate the number if male and females to be born to herd.
Based on target number and number of possible mothers

<details>
<summary>View Source</summary>
```python
@classmethod
def get_total_to_be_born(
    cls, target_num_males: int, target_num_females: int, num_mothers: int
) -> tuple[int, int, int]:
    """Calculate the number if male and females to be born to herd.
    Based on target number and number of possible mothers"""

    def total_to_be_born():
        return target_num_males + target_num_females

    while total_to_be_born() > num_mothers:
        if target_num_males > 0:
            target_num_males -= 1
        if target_num_females > 0:
            target_num_females -= 1

    return target_num_males, target_num_females, total_to_be_born()

```
<details>

`breed_herd(self, sires: list['Animal']) -> base.models.Herd.BreedingResults` builtins.function

> Run a breeding on herd

<details>
<summary>View Source</summary>
```python
def breed_herd(self, sires: list["Animal"]) -> BreedingResults:
    """Run a breeding on herd"""

    NUMBER_OF_MALES = 10
    NUMBER_OF_FEMALES = 70
    MAX_AGE = 5

    mothers = Animal.objects.filter(male=False, herd=self).order_by("?")
    num_males, _num_females, total_to_be_born = self.get_total_to_be_born(
        NUMBER_OF_MALES, NUMBER_OF_FEMALES, len(mothers)
    )

    traitset = Traitset(self.connectedclass.traitset)
    self.breedings += 1

    animals: list[Animal] = []
    for i in range(total_to_be_born):
        male = i < num_males
        sire = sires[i % len(sires)]
        dam = mothers[i]

        animal = Animal.generate_from_breeding_unsaved(
            male, self, traitset, self.connectedclass, sire, dam
        )
        animals.append(animal)

    Animal.objects.bulk_create(animals)
    for animal in animals:
        animal.finalize_animal_unsaved(self)
    Animal.objects.bulk_update(animals, ["name", "pedigree", "inbreeding"])

    all_animals = Animal.objects.defer("pedigree").filter(herd=self)
    recessive_deaths = self.collect_positive_fatal_recessive_animals(
        all_animals, traitset
    )
    age_deaths = self.collect_deaths_from_age(all_animals, MAX_AGE)
    total_dead = set(recessive_deaths + age_deaths)
    for animal in total_dead:
        animal.herd = None

    Animal.objects.bulk_update(total_dead, ["herd"])

    self.connectedclass.update_trend_log(
        new_animals=animals, old_animals=total_dead
    )
    self.save()

    return self.BreedingResults(len(recessive_deaths), len(age_deaths))

```
<details>

`json_dict(self) -> dict[str, typing.Any]` builtins.function

> Get herd as json serializable dict

<details>
<summary>View Source</summary>
```python
def json_dict(self) -> dict[str, Any]:
    """Get herd as json serializable dict"""

    animals = (
        Animal.objects.select_related("connectedclass")
        .defer("pedigree", "connectedclass__trend_log")
        .filter(herd=self)
    )
    num_animals = animals.count()

    summary = {
        nms.GENOTYPE_KEY: defaultdict(int),
        nms.PHENOTYPE_KEY: defaultdict(int),
        nms.PTA_KEY: defaultdict(int),
        nms.NETMERIT_KEY: 0,
    }

    if num_animals > 0:
        for animal in animals:
            summary[nms.NETMERIT_KEY] += animal.net_merit
            for key, val in animal.genotype.items():
                if self.connectedclass.trait_visibility[key][0]:
                    summary[nms.GENOTYPE_KEY][key] += val
            for key, val in animal.phenotype.items():
                if self.connectedclass.trait_visibility[key][1]:
                    summary[nms.PHENOTYPE_KEY][key] += val or 0
            for key, val in animal.ptas.items():
                if self.connectedclass.trait_visibility[key][2]:
                    summary[nms.PTA_KEY][key] += val

        summary[nms.NETMERIT_KEY] = summary[nms.NETMERIT_KEY] / num_animals

        for key, val in summary[nms.GENOTYPE_KEY].items():
            summary[nms.GENOTYPE_KEY][key] = val / num_animals

        for key, val in summary[nms.PHENOTYPE_KEY].items():
            summary[nms.PHENOTYPE_KEY][key] = val / num_animals

        for key, val in summary[nms.PTA_KEY].items():
            summary[nms.PTA_KEY][key] = val / num_animals

    if not self.connectedclass.net_merit_visibility:
        summary.pop(nms.NETMERIT_KEY)

    return {
        nms.NAME_KEY: self.name,
        "connectedclass": self.connectedclass_id,
        "breedings": self.breedings,
        "animals": {x.id: x.json_dict() for x in animals},
        "summary": summary,
    }

```
<details>

`collect_positive_fatal_recessive_animals(self, animals: list['Animal'], traitset: base.traitsets.traitset.Traitset) -> list['Animal']` builtins.function

> Get a list of all animals with fatal genetic recessives

<details>
<summary>View Source</summary>
```python
def collect_positive_fatal_recessive_animals(
    self, animals: list["Animal"], traitset: Traitset
) -> list["Animal"]:
    """Get a list of all animals with fatal genetic recessives"""

    dead = []
    for animal in animals:
        for key, val in animal.recessives.items():
            if val == HOMOZYGOUS_CARRIER_KEY:
                if traitset.find_recessive_or_null(key).fatal:
                    dead.append(animal)

    return dead

```
<details>

`collect_deaths_from_age(self, animals: list['Animal'], maxage: int) -> list['Animal']` builtins.function

> Get a list of all animals that are too old

<details>
<summary>View Source</summary>
```python
def collect_deaths_from_age(
    self, animals: list["Animal"], maxage: int
) -> list["Animal"]:
    """Get a list of all animals that are too old"""

    dead = []
    for animal in animals:
        if self.breedings - animal.generation >= maxage:
            dead.append(animal)

    return dead

```
<details>

## Enrollment(Model)
> Enrollment(id, student, connectedclass, animal, herd)

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

<details>
<summary>View Source</summary>
```python
@classmethod
def create_from_enrollment_request(
    cls, enrollment_request: "EnrollmentRequest"
) -> "Enrollment":
    traitset = Traitset(enrollment_request.connectedclass.traitset)

    if enrollment_request.student.last_name[-1] == "s":
        name = enrollment_request.student.get_full_name() + "' <herd>"
    else:
        name = enrollment_request.student.get_full_name() + "'s <herd>"

    new = cls(
        student=enrollment_request.student,
        connectedclass=enrollment_request.connectedclass,
        animal=enrollment_request.connectedclass.default_animal,
    )
    new.herd = Herd.generate_starter_herd(
        name, 70, 10, traitset, enrollment_request.connectedclass
    )
    new.save()
    new.herd.enrollment = new
    new.herd.save()

    enrollment_request.delete()
    new.connectedclass.update_trend_log(
        save=False,
        new_animals=Animal.objects.defer("pedigree").filter(herd=new.herd),
        old_animals=[],
    )
    new.connectedclass.decrement_enrollment_tokens()

    assignment_fulfilments = []
    for assignment in Assignment.objects.filter(
        connectedclass=new.connectedclass
    ):
        assignment_fulfilments.append(
            AssignmentFulfillment(assignment=assignment, enrollment=new)
        )
    AssignmentFulfillment.objects.bulk_create(assignment_fulfilments)

    return new

```
<details>

`json_dict(self) -> dict[str, typing.Any]` builtins.function

<details>
<summary>View Source</summary>
```python
def json_dict(self) -> dict[str, Any]:
    return {
        "id": self.id,
        "student": {
            "id": self.student.id,
            nms.NAME_KEY: self.student.get_full_name(),
            "email": self.student.email,
        },
        "herd": self.herd_id,
        "connectedclass": self.connectedclass_id,
    }

```
<details>

`get_open_assignments_json_dict(self) -> dict[str, typing.Any]` builtins.function

<details>
<summary>View Source</summary>
```python
def get_open_assignments_json_dict(self) -> dict[str, Any]:
    json = {}

    assignments = Assignment.objects.prefetch_related(
        "assignmentstep_assignment"
    ).filter(
        connectedclass=self.connectedclass,
        startdate__lte=now(),
        duedate__gte=now(),
    )
    for assignment in assignments:
        json[assignment.id] = {
            nms.NAME_KEY: assignment.name,
            "id": assignment.id,
            "startdate": assignment.startdate,
            "duedate": assignment.duedate,
            "steps": [
                {"key": x.step, "verbose": x.verbose_step()}
                for x in sorted(
                    assignment.assignmentstep_assignment.all(),
                    key=lambda y: y.number,
                )
            ],
            "fulfillment": AssignmentFulfillment.objects.get(
                enrollment=self, assignment=assignment
            ).current_step,
        }

    return json

```
<details>

## EnrollmentRequest(Model)
> EnrollmentRequest(id, student, connectedclass)

### Fields
`student_id` django.db.models.fields.related.ForeignKey

`student` django.db.models.fields.related_descriptors.ForwardManyToOneDescriptor

`connectedclass_id` django.db.models.fields.related.ForeignKey

`connectedclass` django.db.models.fields.related_descriptors.ForwardManyToOneDescriptor

### Methods
`create_new(student: django.contrib.auth.models.User, connectedclass: 'Class') -> 'EnrollmentRequest'` builtins.classmethod

<details>
<summary>View Source</summary>
```python
@classmethod
def create_new(
    cls, student: User, connectedclass: "Class"
) -> "EnrollmentRequest":
    new = cls(student=student, connectedclass=connectedclass)
    new.save()
    return new

```
<details>

`json_dict(self) -> dict[str, typing.Any]` builtins.function

<details>
<summary>View Source</summary>
```python
def json_dict(self) -> dict[str, Any]:
    return {
        "id": self.id,
        "student": {
            "id": self.student.id,
            nms.NAME_KEY: self.student.get_full_name(),
            "email": self.student.email,
        },
        "connectedclass": self.connectedclass_id,
    }

```
<details>

## Animal(Model)
> Animal(id, herd, connectedclass, name, generation, male, genomic_tests, genotype, phenotype, ptas, recessives, sire, dam, pedigree, inbreeding, net_merit)

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

<details>
<summary>View Source</summary>
```python
@classmethod
def generate_random_unsaved(
    cls, male: bool, herd: Herd, traitset: Traitset, connectedclass: Class
) -> "Animal":
    new = cls(male=male, herd=herd, connectedclass=connectedclass)

    new.genotype = traitset.get_random_genotype()
    new.net_merit = traitset.derive_net_merit_from_genotype(new.genotype)

    new.phenotype = (
        traitset.get_null_phenotype()
        if male
        else traitset.derive_phenotype_from_genotype(
            new.genotype, new.inbreeding
        )
    )

    new.ptas = traitset.derive_ptas_from_genotype(
        new.genotype, 0, new.genomic_tests
    )
    new.recessives = traitset.get_random_recessives()
    new.pedigree = {
        nms.SIRE_ID_KEY: None,
        nms.DAM_ID_KEY: None,
        nms.ID_KEY: None,
    }

    return new

```
<details>

`generate_from_breeding_unsaved(male: bool, herd: base.models.Herd, traitset: base.traitsets.traitset.Traitset, connectedclass: base.models.Class, sire: 'Animal', dam: 'Animal') -> 'Animal'` builtins.classmethod

<details>
<summary>View Source</summary>
```python
@classmethod
def generate_from_breeding_unsaved(
    cls,
    male: bool,
    herd: Herd,
    traitset: Traitset,
    connectedclass: Class,
    sire: "Animal",
    dam: "Animal",
) -> "Animal":
    new = cls(male=male, herd=herd, connectedclass=connectedclass)
    new.pedigree = {
        nms.SIRE_ID_KEY: sire.pedigree,
        nms.DAM_ID_KEY: dam.pedigree,
        nms.ID_KEY: None,
    }
    new.genotype = traitset.get_genotype_from_breeding(
        sire.genotype, dam.genotype
    )
    new.net_merit = traitset.derive_net_merit_from_genotype(new.genotype)
    new.inbreeding = calculate_inbreeding(new.pedigree)
    new.sire = sire
    new.dam = dam

    new.phenotype = (
        dam.phenotype
        if male
        else traitset.derive_phenotype_from_genotype(
            new.genotype, new.inbreeding
        )
    )

    new.ptas = traitset.derive_ptas_from_genotype(new.genotype, 0, 0)

    new.recessives = traitset.get_recessives_from_breeding(
        sire.recessives, dam.recessives
    )
    new.generation = herd.breedings

    return new

```
<details>

`finalize_animal_unsaved(self, herd: base.models.Herd) -> None` builtins.function

<details>
<summary>View Source</summary>
```python
def finalize_animal_unsaved(self, herd: Herd) -> None:
    if herd.name[-1].lower() == "s":
        self.name = herd.name + "' " + str(self.id)
    else:
        self.name = herd.name + "'s " + str(self.id)

    self.pedigree["id"] = self.id

```
<details>

`resolve_data_key(self, data_key: str | tuple[str, str], connectedclass: Optional[base.models.Class] = None) -> Any` builtins.function

<details>
<summary>View Source</summary>
```python
def resolve_data_key(
    self,
    data_key: str | tuple[str, str],
    connectedclass: Optional[Class] = None,
) -> Any:
    class_traitset = (
        None
        if connectedclass is None
        else Traitset(connectedclass.traitset)
    )

    def adjust_gen(val, uid):
        return (
            val
            if class_traitset is None
            else val
            * class_traitset.find_trait_or_null(uid)
            .animals[connectedclass.default_animal]
            .standard_deviation
        )

    def adjust_phen(val, uid):
        return (
            val
            if class_traitset is None
            else (
                val
                * class_traitset.find_trait_or_null(uid)
                .animals[connectedclass.default_animal]
                .standard_deviation
                * 2
                + class_traitset.find_trait_or_null(uid)
                .animals[connectedclass.default_animal]
                .phenotype_average
                if val is not None
                else None
            )
        )

    def adjust_pta(val, uid):
        return (
            val
            if class_traitset is None
            else val
            * class_traitset.find_trait_or_null(uid)
            .animals[connectedclass.default_animal]
            .standard_deviation
            * 2
            + class_traitset.find_trait_or_null(uid)
            .animals[connectedclass.default_animal]
            .phenotype_average
        )

    if type(data_key) is tuple:
        match data_key[0]:
            case nms.GENOTYPE_KEY:
                return adjust_gen(self.genotype[data_key[1]], data_key[1])
            case nms.PHENOTYPE_KEY:
                return adjust_phen(
                    self.phenotype[data_key[1]], data_key[1]
                )
            case nms.RECESSIVES_KEY:
                return self.recessives[data_key[1]]
            case nms.PTA_KEY:
                return adjust_pta(self.ptas[data_key[1]], data_key[1])
            case nms.FORMATTED_RECESSIVES_KEY:
                match self.recessives[data_key[1]]:
                    case traitset.HOMOZYGOUS_FREE_KEY:
                        return "Tested Free"
                    case traitset.HOMOZYGOUS_CARRIER_KEY:
                        return "Positive"
                    case traitset.HETEROZYGOUS_KEY:
                        return "Carrier"
    else:
        match data_key:
            case nms.HERD_ID_KEY:
                return self.herd.id if self.herd else None
            case nms.HERD_NAME_KEY:
                return self.herd.name if self.herd else None
            case nms.CLASS_ID_KEY:
                return self.connectedclass.id
            case nms.CLASS_NAME_KEY:
                return self.connectedclass.name
            case nms.NAME_KEY:
                return self.name
            case nms.GENERATION_KEY:
                return self.generation
            case nms.SEX_KEY:
                return "male" if self.male else "female"
            case nms.SIRE_ID_KEY:
                return self.sire_id
            case nms.DAM_ID_KEY:
                return self.dam_id
            case nms.INBREEDING_COEFFICIENT_KEY:
                return self.inbreeding
            case nms.INBREEDING_PERCENTAGE_KEY:
                return self.inbreeding * 100
            case nms.GENOTYPE_KEY:
                return self.genotype
            case nms.PHENOTYPE_KEY:
                return self.phenotype
            case nms.RECESSIVES_KEY:
                return self.recessives
            case nms.MALE_KEY:
                return self.male
            case nms.NETMERIT_KEY:
                return self.net_merit
            case nms.ID_KEY:
                return self.id

```
<details>

`json_dict(self) -> dict[str, typing.Any]` builtins.function

<details>
<summary>View Source</summary>
```python
def json_dict(self) -> dict[str, Any]:
    json = {}

    data_keys = [
        nms.ID_KEY,
        nms.NAME_KEY,
        nms.GENERATION_KEY,
        nms.DAM_ID_KEY,
        nms.SIRE_ID_KEY,
        nms.INBREEDING_COEFFICIENT_KEY,
        nms.MALE_KEY,
    ] + (
        [nms.NETMERIT_KEY]
        if self.connectedclass.net_merit_visibility
        else []
    )

    for data_key in data_keys:
        json[data_key] = self.resolve_data_key(data_key)

    return json | {
        nms.GENOTYPE_KEY: {
            key: val
            for key, val in self.genotype.items()
            if self.connectedclass.trait_visibility[key][0]
        },
        nms.PHENOTYPE_KEY: {
            key: val
            for key, val in self.phenotype.items()
            if self.connectedclass.trait_visibility[key][1]
        },
        nms.PTA_KEY: {
            key: val
            for key, val in self.ptas.items()
            if self.connectedclass.trait_visibility[key][2]
            and (self.male or not self.connectedclass.hide_female_pta)
        },
        nms.RECESSIVES_KEY: {
            key: val
            for key, val in self.recessives.items()
            if self.connectedclass.recessive_visibility[key]
        },
    }

```
<details>

`recalculate_pta_unsaved(self, number_of_daughters: int, traitset: base.traitsets.traitset.Traitset)` builtins.function

<details>
<summary>View Source</summary>
```python
def recalculate_pta_unsaved(
    self, number_of_daughters: int, traitset: Traitset
):
    self.ptas = traitset.derive_ptas_from_genotype(
        self.genotype, number_of_daughters, self.genomic_tests
    )

```
<details>

## Assignment(Model)
> Assignment(id, connectedclass, startdate, duedate, name)

### Fields
`connectedclass_id` django.db.models.fields.related.ForeignKey

`connectedclass` django.db.models.fields.related_descriptors.ForwardManyToOneDescriptor

`startdate` django.db.models.fields.DateTimeField

`duedate` django.db.models.fields.DateTimeField

`name` django.db.models.fields.CharField

### Methods
`create_new(name: str, startdate: datetime.datetime, duedate: datetime.datetime, steps: list[str], connectedclass: base.models.Class) -> 'Assignment'` builtins.classmethod

<details>
<summary>View Source</summary>
```python
@classmethod
def create_new(
    cls,
    name: str,
    startdate: datetime,
    duedate: datetime,
    steps: list[str],
    connectedclass: Class,
) -> "Assignment":
    new = cls(
        name=name,
        startdate=startdate,
        duedate=duedate,
        connectedclass=connectedclass,
    )
    new.save()

    assignment_fulfilments = []
    for enrollment in Enrollment.objects.filter(
        connectedclass=connectedclass
    ):
        assignment_fulfilments.append(
            AssignmentFulfillment(enrollment=enrollment, assignment=new)
        )
    AssignmentFulfillment.objects.bulk_create(assignment_fulfilments)

    assignment_steps = []
    for idx, step in enumerate(steps):
        assignment_steps.append(
            AssignmentStep(number=idx, assignment=new, step=step)
        )
    AssignmentStep.objects.bulk_create(assignment_steps)

    return new

```
<details>

## AssignmentStep(Model)
> AssignmentStep(id, assignment, step, number)

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

<details>
<summary>View Source</summary>
```python
def verbose_step(self) -> Optional[str]:
    for key, val in self.CHOICES:
        if self.step == key:
            return val

```
<details>

## AssignmentFulfillment(Model)
> AssignmentFulfillment(id, enrollment, assignment, current_step)

### Fields
`enrollment_id` django.db.models.fields.related.ForeignKey

`enrollment` django.db.models.fields.related_descriptors.ForwardManyToOneDescriptor

`assignment_id` django.db.models.fields.related.ForeignKey

`assignment` django.db.models.fields.related_descriptors.ForwardManyToOneDescriptor

`current_step` django.db.models.fields.IntegerField

### Methods
