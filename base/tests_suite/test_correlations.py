from django.test import TestCase
from ..traitsets import Traitset, REGISTERED
from ..traitsets.traitset import Trait, Recessive
from random import random


class TestCorrelations(TestCase):
