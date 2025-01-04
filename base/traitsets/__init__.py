from .registration import Registration
from .traitset import Traitset, DOCUMENTED_FUNCS

registered = [
    Registration("ANIMAL_SCIENCE_322", True),
    Registration("STANDARD_A", False),
    Registration("ANIMAL_SCIENCE_422", True),
]

TRAITSET_CHOICES = [(x, x) for x in registered if x.enabled]
