from .registration import Registration
from .traitset import Traitset, DOCUMENTED_FUNCS

REGISTERED = [
    Registration("ANIMAL_SCIENCE_322", True),
    Registration("STANDARD_A", False),
    Registration("ANIMAL_SCIENCE_422", True),
]

TRAITSET_CHOICES = [(x, x) for x in REGISTERED if x.enabled]
