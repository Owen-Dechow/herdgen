from collections import defaultdict
from typing import Any, Optional
from django.db import models
from django.contrib.auth.models import User
from random import choice
from django.utils.timezone import now

from .traitsets import Traitset
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
    trend_log = models.JSONField(default=dict)
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

        new.save()

        return new

    def decrement_enrollment_tokens(self):
        self.enrollment_tokens -= 1
        self.save()


class Herd(models.Model):
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

    def breed_herd(self, sires: list["Animal"]) -> None:
        NUMBER_OF_MALES = 10
        NUMBER_OF_FEMALES = 70
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

        self.save()

    def json_dict(self) -> dict[str | Any]:
        animals = Animal.objects.filter(herd=self)
        num_animals = animals.count()

        summary = {"genotype": defaultdict(int), "phenotype": defaultdict(int)}
        for animal in animals:
            for key, val in animal.genotype.items():
                if self.connectedclass.trait_visibility[key][0]:
                    summary["genotype"][key] += val
            for key, val in animal.phenotype.items():
                if self.connectedclass.trait_visibility[key][1]:
                    summary["phenotype"][key] += val

        for key, val in summary["genotype"].items():
            summary["genotype"][key] = val / num_animals

        for key, val in summary["phenotype"].items():
            summary["phenotype"][key] = val / num_animals

        return {
            "name": self.name,
            "connectedclass": self.connectedclass_id,
            "breedings": self.breedings,
            "animals": {x.id: x.json_dict() for x in Animal.objects.filter(herd=self)},
            "summary": summary,
        }


class Enrollment(models.Model):
    student = models.ForeignKey(to=User, on_delete=models.CASCADE)
    connectedclass = models.ForeignKey(to="Class", on_delete=models.CASCADE)
    animal = models.CharField(max_length=255)
    herd = models.ForeignKey(
        to="Herd", on_delete=models.CASCADE, related_name="enrollment_herd"
    )

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
        )
        new.herd = Herd.generate_starter_herd(
            name, 70, 10, traitset, enrollment_request.connectedclass
        )
        new.save()
        new.herd.enrollment = new
        new.herd.save()

        enrollment_request.delete()
        new.connectedclass.decrement_enrollment_tokens()

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

    def get_open_assignments_json_dict(self) -> dict[str | Any]:
        json = {}

        assignments = Assignment.objects.filter(
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
                    for x in AssignmentStep.objects.filter(
                        assignment=assignment
                    ).order_by("number")
                ],
                "fulfillment": AssignmentFulfillment.objects.get(
                    enrollment=self, assignment=assignment
                ).current_step,
            }

        return json


class EnrollmentRequest(models.Model):
    student = models.ForeignKey(to=User, on_delete=models.CASCADE)
    connectedclass = models.ForeignKey(to="Class", on_delete=models.CASCADE)

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
    herd = models.ForeignKey(to="Herd", on_delete=models.SET_NULL, null=True)
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

    @classmethod
    def generate_random_unsaved(
        cls, male: bool, herd: Herd, traitset: Traitset, connectedclass: Class
    ) -> "Animal":
        new = cls(male=male, herd=herd, connectedclass=connectedclass)

        new.genotype = traitset.get_random_genotype()
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

    def json_dict(self) -> dict[str | Any]:
        return {
            "id": self.id,
            "name": self.name,
            "generation": self.generation,
            "male": self.male,
            "genotype": {
                key: val
                for key, val in self.genotype.items()
                if self.connectedclass.trait_visibility[key][0]
            },
            "phenotype": {
                key: val
                for key, val in self.phenotype.items()
                if self.connectedclass.trait_visibility[key][1]
            },
            "recessives": {
                key: val
                for key, val in self.recessives.items()
                if self.connectedclass.recessive_visibility[key]
            },
            "dam": self.dam_id,
            "sire": self.sire_id,
            "inbreeding": self.inbreeding,
        }


class Assignment(models.Model):
    connectedclass = models.ForeignKey(to="Class", on_delete=models.CASCADE)
    startdate = models.DateTimeField(null=True, blank=True)
    duedate = models.DateTimeField(null=True, blank=True)
    name = models.CharField(max_length=255)


class AssignmentStep(models.Model):
    CHOICE_MALE_SUBMISSION = "msub"
    CHOICE_FEMALE_SUBMISSION = "fsub"
    CHOICE_BREED = "breed"

    CHOICES = (
        (CHOICE_MALE_SUBMISSION, "Submit Male"),
        (CHOICE_FEMALE_SUBMISSION, "Submit Female"),
        (CHOICE_BREED, "Breed"),
    )

    assignment = models.ForeignKey(to="Assignment", on_delete=models.CASCADE)
    step = models.CharField(choices=CHOICES, max_length=255)
    number = models.IntegerField()

    def verbose_step(self) -> Optional[str]:
        for key, val in self.CHOICES:
            if self.step == key:
                return val


class AssignmentFulfillment(models.Model):
    enrollment = models.ForeignKey(to="Enrollment", on_delete=models.CASCADE)
    assignment = models.ForeignKey(to="Assignment", on_delete=models.CASCADE)
    current_step = models.IntegerField(default=0)
