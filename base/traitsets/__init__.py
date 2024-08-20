from .registration import Registration
from .traitset import Traitset

registered = [
    Registration("STANDARD_A", True),
]

TRAISET_CHOICES = [(x, x) for x in registered if x.enabled]
