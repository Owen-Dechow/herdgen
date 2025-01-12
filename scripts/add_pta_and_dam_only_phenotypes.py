from base.traitsets.traitset import Traitset
from .add_pta_visibility_defaults import add_pta_visibility_defaults
from base.models import Animal


def add_pta_and_dam_only_phenotypes():
    add_pta_visibility_defaults()

    traitsets = {}
    animals = Animal.objects.select_related("connectedclass").all()
    count = Animal.objects.count()
    print(f"{(count)} Animals to process")

    for idx, anim in enumerate(animals.iterator(chunk_size=50)):
        if anim.connectedclass_id in traitsets:
            traitset = traitsets[anim.connectedclass_id]
        else:
            traitset = Traitset(anim.connectedclass.traitset)
            traitsets[anim.connectedclass_id] = traitset

        anim.ptas = traitset.derive_ptas_from_genotype(anim.genotype, 0, 0)

        anim.save()
        print(f"Animal {idx + 1}/{count} {(idx - 1)/count * 100}%")
