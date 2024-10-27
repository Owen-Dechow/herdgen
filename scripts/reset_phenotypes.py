from base import models
from base.traitsets import Traitset


def run():
    sets: dict[int, Traitset] = {}

    for klass in models.Class.objects.all():
        sets[klass.id] = Traitset(klass.traitset)

    animals = models.Animal.objects.all()
    for animal in animals:
        traitset = sets[animal.connectedclass_id]
        animal.phenotype = traitset.derive_phenotype_from_genotype(
            animal.genotype, animal.inbreeding
        )

    models.Animal.objects.bulk_update(animals, ["phenotype"])
