from collections import defaultdict
import enum
from typing import Any, Optional
from django.db import models
from django.contrib.auth.models import User
from random import choice
from django.utils.timezone import now, datetime

from .traitsets import Traitset
from .traitsets import traitset
from .traitsets.traitset import HOMOZYGOUS_CARRIER_KEY
from .inbreeding import calculate_inbreeding


# Create your models here.
class Class(models.Model):
    name = models.CharField(max_length=255)
    teacher = models.ForeignKey(to=User, on_delete=models.CASCADE)
    traitset = models.CharField(max_length=255)
    info = models.TextField(blank=True, null=True)
    classcode = models.CharField(max_length=255)
    trait_visibility = models.JSONField()
    recessive_visibility = models.JSONField()
    net_merit_visibility = models.BooleanField(default=True)
    trend_log = models.JSONField(default=list, blank=True)
    default_animal = models.CharField(max_length=255)
    allow_other_animals = models.BooleanField(default=True)
    starter_herd = models.ForeignKey(
        to="Herd",
        on_delete=models.CASCADE,
        related_name="class_starter_herd",
        null=True,
    )
    class_herd = models.ForeignKey(
        to="Herd",
        on_delete=models.CASCADE,
        related_name="class_class_herd",
        null=True,
    )
    enrollment_tokens = models.IntegerField(default=0)

    TIME_STAMP_KEY = "timestamp"
    POPULATION_SIZE_KEY = "populationsize"

    def __str__(self) -> str:
        return f"{self.id} | {self.name}"

    @classmethod
    def generate_class_code(cls) -> str:
        CHARACTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
        SECTIONS = 3
        SECTION_LENGTH = 3
        return "-".join(
            [
                "".join([choice(CHARACTERS) for _ in range(SECTION_LENGTH)])
                for _ in range(SECTIONS)
            ]
        )

    @classmethod
    def create_new(cls, user: User, name: str, traitsetname: str, info: str) -> "Class":
        new = cls(name=name, traitset=traitsetname, info=info, teacher=user)
        new.classcode = cls.generate_class_code()

        traitset = Traitset(traitsetname)
        new.trait_visibility = traitset.get_default_trait_visibility()
        new.recessive_visibility = traitset.get_default_recessive_visibility()
        new.default_animal = traitset.animal_choices[0][0]
        new.save()

        new.starter_herd = Herd.generate_starter_herd(
            name=f"{name} starter <herd>",
            females=10,
            males=30,
            traitset=traitset,
            connectedclass=new,
        )
        new.class_herd = Herd.generate_empty_herd(
            name=f"{name} class <herd>",
            connectedclass=new,
        )

        new.update_trend_log(save=False)

        new.save()

        return new

    def decrement_enrollment_tokens(self):
        self.enrollment_tokens -= 1
        self.save()

    def get_open_assignments(self) -> models.manager.BaseManager["Assignment"]:
        return Assignment.objects.filter(
            connectedclass=self, startdate__lte=now(), duedate__gte=now()
        )

    def update_trend_log(self, save: bool = True) -> None:
        capture = {"genotype": defaultdict(int), "phenotype": defaultdict(int)}
        net_merit_capture = 0

        animals = Animal.objects.filter(connectedclass=self)
        num_animals_alive = 0
        for animal in animals:

            if animal.herd_id is None:
                continue
            else:
                num_animals_alive += 1

            net_merit_capture += animal.net_merit

            for key, val in animal.genotype.items():
                capture["genotype"][key] += val

            for key, val in animal.phenotype.items():
                capture["phenotype"][key] += val

        net_merit_capture = net_merit_capture / num_animals_alive

        for key, val in capture["genotype"].items():
            capture["genotype"][key] = val / num_animals_alive

        for key, val in capture["phenotype"].items():
            capture["phenotype"][key] = val / num_animals_alive

        capture[self.TIME_STAMP_KEY] = now().isoformat()
        capture[self.POPULATION_SIZE_KEY] = num_animals_alive
        capture[Animal.DataKeys.NetMerit.value] = net_merit_capture
        self.trend_log.append(capture)

        if save:
            self.save()


class Herd(models.Model):
    class BreedingResults:
        recessive_deaths: int
        age_deaths: int

        def __init__(self, recessive_deaths, age_deaths):
            self.recessive_deaths = recessive_deaths
            self.age_deaths = age_deaths

    name = models.CharField(max_length=255)
    connectedclass = models.ForeignKey(to="Class", on_delete=models.CASCADE, null=True)
    breedings = models.IntegerField(default=0)
    enrollment = models.ForeignKey(
        to="Enrollment",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="herd_enrollment",
    )

    def __str__(self) -> str:
        return f"{self.id} | {self.name}"

    @classmethod
    def generate_starter_herd(
        cls,
        name: str,
        females: int,
        males: int,
        traitset: Traitset,
        connectedclass: Class,
    ) -> "Herd":
        new = cls(name=name, connectedclass=connectedclass)
        new.save()

        males = [
            Animal.generate_random_unsaved(True, new, traitset, connectedclass)
            for _ in range(males)
        ]
        females = [
            Animal.generate_random_unsaved(False, new, traitset, connectedclass)
            for _ in range(females)
        ]

        Animal.objects.bulk_create(males + females)
        for animal in males + females:
            animal.finalize_animal_unsaved(new)
        Animal.objects.bulk_update(males + females, ["name", "pedigree", "inbreeding"])

        return new

    @classmethod
    def generate_empty_herd(cls, name: str, connectedclass: Class) -> "Herd":
        new = cls(name=name, connectedclass=connectedclass)
        new.save()

        return new

    @classmethod
    def get_total_to_be_born(
        cls, target_num_males: int, target_num_females: int, num_mothers: int
    ) -> tuple[int, int, int]:
        total_to_be_born = lambda: target_num_males + target_num_females

        while total_to_be_born() > num_mothers:
            if target_num_males > 0:
                target_num_males -= 1
            if target_num_females > 0:
                target_num_females -= 1

        return target_num_males, target_num_females, total_to_be_born()

    def breed_herd(self, sires: list["Animal"]) -> BreedingResults:
        NUMBER_OF_MALES = 10
        NUMBER_OF_FEMALES = 70
        MAX_AGE = 5

        mothers = Animal.objects.filter(male=False, herd=self).order_by("?")
        num_males, num_females, total_to_be_born = self.get_total_to_be_born(
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

        all_animals = Animal.objects.filter(herd=self)
        recessive_deaths = self.collect_positive_fatal_recessive_animals(
            all_animals, traitset
        )
        age_deaths = self.collect_deaths_from_age(all_animals, MAX_AGE)
        total_dead = set(recessive_deaths + age_deaths)
        for animal in total_dead:
            animal.herd = None

        Animal.objects.bulk_update(total_dead, ["herd"])

        self.connectedclass.update_trend_log()
        self.save()

        return self.BreedingResults(len(recessive_deaths), len(age_deaths))

    def json_dict(self) -> dict[str | Any]:
        animals = Animal.objects.select_related("connectedclass").filter(herd=self)
        num_animals = animals.count()

        summary = {
            "genotype": defaultdict(int),
            "phenotype": defaultdict(int),
            Animal.DataKeys.NetMerit.value: 0,
        }

        if num_animals > 0:
            for animal in animals:
                summary[Animal.DataKeys.NetMerit.value] += animal.net_merit
                for key, val in animal.genotype.items():
                    if self.connectedclass.trait_visibility[key][0]:
                        summary["genotype"][key] += val
                for key, val in animal.phenotype.items():
                    if self.connectedclass.trait_visibility[key][1]:
                        summary["phenotype"][key] += val

            summary[Animal.DataKeys.NetMerit.value] = (
                summary[Animal.DataKeys.NetMerit.value] / num_animals
            )

            for key, val in summary["genotype"].items():
                summary["genotype"][key] = val / num_animals

            for key, val in summary["phenotype"].items():
                summary["phenotype"][key] = val / num_animals

        if not self.connectedclass.net_merit_visibility:
            summary.pop(Animal.DataKeys.NetMerit.value)

        return {
            "name": self.name,
            "connectedclass": self.connectedclass_id,
            "breedings": self.breedings,
            "animals": {x.id: x.json_dict() for x in animals},
            "summary": summary,
        }

    def collect_positive_fatal_recessive_animals(
        self, animals: list["Animal"], traitset: Traitset
    ) -> list["Animal"]:
        dead = []
        for animal in animals:
            for key, val in animal.recessives.items():
                if val == HOMOZYGOUS_CARRIER_KEY:
                    if traitset.find_recessive_or_null(key).fatal:
                        dead.append(animal)

        return dead

    def collect_deaths_from_age(
        self, animals: list["Animal"], maxage: int
    ) -> list["Animal"]:
        dead = []
        for animal in animals:
            if self.breedings - animal.generation >= maxage:
                dead.append(animal)

        return dead


class Enrollment(models.Model):
    student = models.ForeignKey(to=User, on_delete=models.CASCADE)
    connectedclass = models.ForeignKey(to="Class", on_delete=models.CASCADE)
    animal = models.CharField(max_length=255)
    herd = models.ForeignKey(
        to="Herd", on_delete=models.CASCADE, related_name="enrollment_herd"
    )

    def __str__(self) -> str:
        return f"{self.id} | {self.student.email} in {self.connectedclass.name}"

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
        new.connectedclass.update_trend_log(save=False)
        new.connectedclass.decrement_enrollment_tokens()

        assignment_fulfillments = []
        for assignment in Assignment.objects.filter(connectedclass=new.connectedclass):
            assignment_fulfillments.append(
                AssignmentFulfillment(assignment=assignment, enrollment=new)
            )
        AssignmentFulfillment.objects.bulk_create(assignment_fulfillments)

        return new

    def json_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "student": {
                "id": self.student.id,
                "name": self.student.get_full_name(),
                "email": self.student.email,
            },
            "herd": self.herd_id,
            "connectedclass": self.connectedclass_id,
        }

    def get_open_assignments_json_dict(self) -> dict[str | Any]:
        json = {}

        assignments = Assignment.objects.prefetch_related(
            "assignmentstep_assignment"
        ).filter(
            connectedclass=self.connectedclass, startdate__lte=now(), duedate__gte=now()
        )
        for assignment in assignments:
            json[assignment.id] = {
                "name": assignment.name,
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


class EnrollmentRequest(models.Model):
    student = models.ForeignKey(to=User, on_delete=models.CASCADE)
    connectedclass = models.ForeignKey(to="Class", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.id} | {self.student.email} for {self.connectedclass.name}"

    @classmethod
    def create_new(cls, student: User, connectedclass: "Class") -> "EnrollmentRequest":
        new = cls(student=student, connectedclass=connectedclass)
        new.save()
        return new

    def json_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "student": {
                "id": self.student.id,
                "name": self.student.get_full_name(),
                "email": self.student.email,
            },
            "connectedclass": self.connectedclass_id,
        }


class Animal(models.Model):
    class DataKeys(enum.Enum):
        HerdId = "herd"
        HerdName = "herdname"
        ClassId = "class"
        ClassName = "classname"
        Name = "name"
        Generation = "generation"
        Sex = "sex"
        SireId = "sire"
        DamId = "dam"
        InbreedingCoefficient = "inbreeding"
        InbreedingPercentage = "inbreedingpercentage"
        Genotype = "genotype"
        Phenotype = "phenotype"
        Recessives = "recessives"
        NiceRecessives = "nicerecessive"
        Male = "male"
        Id = "id"
        NetMerit = "NM$"

    herd = models.ForeignKey(to="Herd", on_delete=models.CASCADE, null=True)
    connectedclass = models.ForeignKey(to="Class", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    generation = models.IntegerField(default=0)
    male = models.BooleanField()

    genotype = models.JSONField()
    phenotype = models.JSONField()
    recessives = models.JSONField()

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

    pedigree = models.JSONField()
    inbreeding = models.FloatField(default=0)
    net_merit = models.FloatField()

    def __str__(self) -> str:
        return f"{self.id} | {self.name}"

    @classmethod
    def generate_random_unsaved(
        cls, male: bool, herd: Herd, traitset: Traitset, connectedclass: Class
    ) -> "Animal":
        new = cls(male=male, herd=herd, connectedclass=connectedclass)

        new.genotype = traitset.get_random_genotype()
        new.net_merit = traitset.derive_net_merit_from_genotype(new.genotype)
        new.phenotype = traitset.derive_phenotype_from_genotype(
            new.genotype, new.inbreeding
        )
        new.recessives = traitset.get_random_recessives()
        new.pedigree = {"sire": None, "dam": None, "id": None}

        return new

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
        new.pedigree = {"sire": sire.pedigree, "dam": dam.pedigree, "id": None}
        new.genotype = traitset.get_genotype_from_breeding(sire.genotype, dam.genotype)
        new.net_merit = traitset.derive_net_merit_from_genotype(new.genotype)
        new.inbreeding = calculate_inbreeding(new.pedigree)
        new.phenotype = traitset.derive_phenotype_from_genotype(
            new.genotype, new.inbreeding
        )
        new.recessives = traitset.get_recessives_from_breeding(
            sire.recessives, dam.recessives
        )
        new.generation = herd.breedings

        return new

    def finalize_animal_unsaved(self, herd: Herd) -> None:
        if herd.name[-1].lower() == "s":
            self.name = herd.name + "' " + str(self.id)
        else:
            self.name = herd.name + "'s " + str(self.id)

        self.pedigree["id"] = self.id

    def resolve_data_key(
        self,
        data_key: DataKeys | tuple[DataKeys, str],
        connectedclass: Optional[Class] = None,
    ) -> Any:
        class_traitset = None if connectedclass is None else Traitset(connectedclass.traitset)
        adjust_gen = lambda val, uid: (
            val
            if class_traitset is None
            else val
            * class_traitset.find_trait_or_null(uid)
            .animals[connectedclass.default_animal]
            .standard_deviation
        )

        adjust_phen = lambda val, uid: (
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
                case self.DataKeys.Genotype:
                    return adjust_gen(self.genotype[data_key[1]], data_key[1])
                case self.DataKeys.Phenotype:
                    return adjust_phen(self.phenotype[data_key[1]], data_key[1])
                case self.DataKeys.Recessives:
                    return self.recessives[data_key[1]]
                case self.DataKeys.NiceRecessives:
                    match self.recessives[data_key[1]]:
                        case traitset.HOMOZYGOUS_FREE_KEY:
                            return "Homozygous Free"
                        case traitset.HOMOZYGOUS_CARRIER_KEY:
                            return "Homozygous Carrier"
                        case traitset.HETEROZYGOUS_KEY:
                            return "Heterozygous"
        else:
            match data_key:
                case self.DataKeys.HerdId:
                    return self.herd.id if self.herd else None
                case self.DataKeys.HerdName:
                    return self.herd.name if self.herd else None
                case self.DataKeys.ClassId:
                    return self.connectedclass.id
                case self.DataKeys.ClassName:
                    return self.connectedclass.name
                case self.DataKeys.Name:
                    return self.name
                case self.DataKeys.Generation:
                    return self.generation
                case self.DataKeys.Sex:
                    return "male" if self.male else "female"
                case self.DataKeys.SireId:
                    sire = self.pedigree["sire"]
                    if sire is not None:
                        return sire["id"]
                case self.DataKeys.DamId:
                    dam = self.pedigree["dam"]
                    if dam is not None:
                        return dam["id"]
                case self.DataKeys.InbreedingCoefficient:
                    return self.inbreeding
                case self.DataKeys.InbreedingPercentage:
                    return self.inbreeding * 100
                case self.DataKeys.Genotype:
                    return self.genotype
                case self.DataKeys.Phenotype:
                    return self.phenotype
                case self.DataKeys.Recessives:
                    return self.recessives
                case self.DataKeys.Male:
                    return self.male
                case self.DataKeys.NetMerit:
                    return self.net_merit
                case self.DataKeys.Id:
                    return self.id

    def json_dict(self) -> dict[str | Any]:

        DataKeys = self.DataKeys
        json = {}

        data_keys = [
            DataKeys.Id,
            DataKeys.Name,
            DataKeys.Generation,
            DataKeys.Male,
            DataKeys.DamId,
            DataKeys.SireId,
            DataKeys.InbreedingCoefficient,
        ] + ([DataKeys.NetMerit] if self.connectedclass.net_merit_visibility else [])

        for data_key in data_keys:
            json[data_key.value] = self.resolve_data_key(data_key)

        return json | {
            DataKeys.Genotype.value: {
                key: val
                for key, val in self.genotype.items()
                if self.connectedclass.trait_visibility[key][0]
            },
            DataKeys.Phenotype.value: {
                key: val
                for key, val in self.phenotype.items()
                if self.connectedclass.trait_visibility[key][1]
            },
            DataKeys.Recessives.value: {
                key: val
                for key, val in self.recessives.items()
                if self.connectedclass.recessive_visibility[key]
            },
        }


class Assignment(models.Model):
    connectedclass = models.ForeignKey(to="Class", on_delete=models.CASCADE)
    startdate = models.DateTimeField(null=True, blank=True)
    duedate = models.DateTimeField(null=True, blank=True)
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.id} | {self.name} for {self.connectedclass.name}"

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

        assignment_fulfillments = []
        for enrollment in Enrollment.objects.filter(connectedclass=connectedclass):
            assignment_fulfillments.append(
                AssignmentFulfillment(enrollment=enrollment, assignment=new)
            )
        AssignmentFulfillment.objects.bulk_create(assignment_fulfillments)

        assignment_steps = []
        for idx, step in enumerate(steps):
            assignment_steps.append(
                AssignmentStep(number=idx, assignment=new, step=step)
            )
        AssignmentStep.objects.bulk_create(assignment_steps)

        return new


class AssignmentStep(models.Model):
    CHOICE_MALE_SUBMISSION = "msub"
    CHOICE_FEMALE_SUBMISSION = "fsub"
    CHOICE_BREED = "breed"

    CHOICES = (
        (CHOICE_MALE_SUBMISSION, "Submit Male"),
        (CHOICE_FEMALE_SUBMISSION, "Submit Female"),
        (CHOICE_BREED, "Breed"),
    )

    assignment = models.ForeignKey(
        to="Assignment",
        related_name="assignmentstep_assignment",
        on_delete=models.CASCADE,
    )
    step = models.CharField(choices=CHOICES, max_length=255)
    number = models.IntegerField()

    def __str__(self) -> str:
        return f"{self.id} | {self.step} for {self.assignment.name}"

    def verbose_step(self) -> Optional[str]:
        for key, val in self.CHOICES:
            if self.step == key:
                return val


class AssignmentFulfillment(models.Model):
    enrollment = models.ForeignKey(to="Enrollment", on_delete=models.CASCADE)
    assignment = models.ForeignKey(to="Assignment", on_delete=models.CASCADE)
    current_step = models.IntegerField(default=0)

    def __str__(self) -> str:
        return f"{self.id} | {self.assignment.name} for {self.enrollment.student.email}"
