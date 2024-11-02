from json import dumps
from django import template
from django.utils.safestring import mark_safe, SafeText
from typing import Any

from .. import models
from ..traitsets import Traitset
from ..traitsets.traitset import TraitsetAnimalFilter

register = template.Library()


class ContextCast:
    traitset: Traitset
    animal: str
    animalfilter: TraitsetAnimalFilter

    def __init__(self, context: dict[str, Any] | None):
        if context is None:
            return

        if enrollment := context.get("enrollment", None):
            self.traitset = Traitset(enrollment.connectedclass.traitset)
            self.animal = enrollment.animal

        elif connectedclass := context.get("connectedclass", None):
            self.traitset = Traitset(connectedclass.traitset)
            self.animal = connectedclass.default_animal

        elif connectedclass := context.get("class", None):
            self.traitset = Traitset(connectedclass.traitset)
            self.animal = connectedclass.default_animal

        self.animalfilter = self.traitset.animals[self.animal]

    @classmethod
    def from_class(cls, connectedclass: models.Class) -> "ContextCast":
        new = cls(None)

        new.traitset = Traitset(connectedclass.traitset)
        new.animal = connectedclass.default_animal
        new.animalfilter = new.traitset.animals[new.animal]
        return new


def get_filter_dict(
    contextcast: ContextCast,
) -> dict[str, dict[str, str] | dict[str, Any] | str]:
    filter_dict = {
        "herds": contextcast.animalfilter.herds,
        "herd": contextcast.animalfilter.herd,
        "male": contextcast.animalfilter.male,
        "males": contextcast.animalfilter.males,
        "female": contextcast.animalfilter.female,
        "females": contextcast.animalfilter.females,
        "sire": contextcast.animalfilter.sire,
        "sires": contextcast.animalfilter.sires,
        "dam": contextcast.animalfilter.dam,
        "dams": contextcast.animalfilter.dams,
        "phenotype_prefix": contextcast.animalfilter.phenotype_prefix,
        "genotype_prefix": contextcast.animalfilter.genotype_prefix,
    }

    cap_filter_dict = {}
    for key, val in filter_dict.items():
        cap_key = key[0].upper() + key[1:]
        cap_val = val[0].upper() + val[1:]
        cap_filter_dict[cap_key] = cap_val

    return (
        filter_dict
        | {
            x.uid: {
                "name": x.animals[contextcast.animal].name,
                "standard_deviation": x.animals[contextcast.animal].standard_deviation,
                "phenotype_average": x.animals[contextcast.animal].phenotype_average,
                "unit": x.animals[contextcast.animal].unit,
            }
            for x in contextcast.traitset.traits
        }
        | {
            x.uid: {
                "name": x.animals[contextcast.animal].name,
            }
            for x in contextcast.traitset.recessives
        }
        | cap_filter_dict
    )


@register.simple_tag(takes_context=True)
def load_filter_dict(context: dict[str, Any]) -> SafeText:
    contextcast = ContextCast(context)
    safe_text: SafeText = mark_safe(
        f"<script>var Filter = {dumps(get_filter_dict(contextcast))}</script>"
    )
    return safe_text


@register.simple_tag(takes_context=True)
def auto_filter_text(context: dict[str, Any], text: str) -> str:
    contextcast = ContextCast(context)

    for key, val in get_filter_dict(contextcast).items():
        if type(val) is dict:
            text = text.replace(f"<{key}>", val["name"])
        else:
            text = text.replace(f"<{key}>", val)

    return text


def filter_text_to_default(text: str, connectedclass: models.Class):
    contextcast = ContextCast.from_class(connectedclass)

    for key, val in get_filter_dict(contextcast).items():
        if type(val) is dict:
            text = text.replace(f"<{key}>", val["name"])
        else:
            text = text.replace(f"<{key}>", val)

    return text
