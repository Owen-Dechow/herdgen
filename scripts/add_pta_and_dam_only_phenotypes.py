from base.traitsets.traitset import Traitset
from .add_pta_visibility_defaults import add_pta_visibility_defaults
from base.models import Animal, Class


def add_pta_and_dam_only_phenotypes():
    add_pta_visibility_defaults()
    for klass in Class.objects.all():
        klass.recalculate_ptas()

    traitsets = {}
    animals = Animal.objects.select_related("connectedclass").filter(herd=None)
    for anim in animals:
        if anim.connectedclass_id in traitsets:
            traitset = traitsets[anim.connectedclass_id]
        else:
            traitset = Traitset(anim.connectedclass.traitset)
            traitsets[anim.connectedclass_id] = traitset

        anim.ptas = traitset.derive_ptas_from_genotype(anim.genotype, 0, 0)

    Animal.objects.bulk_update(animals, ["ptas"])
