from django.test import TestCase
from ..traitsets import Traitset, TRAITSET_CHOICES
from ..traitsets.traitset import Trait, Recessive
from random import random


class TestTraitsets(TestCase):
    def _test_on_each(self, func):
        for registration, _ in TRAITSET_CHOICES:
            if registration.enabled:
                traitset = Traitset(registration.name)
                func(traitset)

    def test_traitset_loading(self):
        self._test_on_each(lambda x: None)

    def test_get_random_genotype(self):
        def test(x: Traitset):
            gen = x.get_random_genotype()

            for t in x.traits:
                self.assertIn(t.uid, gen)

        self._test_on_each(test)

    def test_get_random_recessive(self):
        def test(x: Traitset):
            rec = x.get_random_recessives()

            for r in x.recessives:
                self.assertIn(r.uid, rec)

        self._test_on_each(test)

    def test_derive_phenotype_from_genotype(self):
        def test(x: Traitset):
            gen = x.get_random_genotype()
            ic = 0.1
            phen = x.derive_phenotype_from_genotype(gen, ic)

            for k in gen:
                self.assertIn(k, phen)

        self._test_on_each(test)

    def test_get_default_trait_visiblity(self):
        def test(x: Traitset):
            vis = x.get_default_trait_visibility()

            for t in x.traits:
                self.assertIn(t.uid, vis)

        self._test_on_each(test)

    def test_get_default_recessive_visibility(self):
        def test(x: Traitset):
            vis = x.get_default_recessive_visibility()

            for r in x.recessives:
                self.assertIn(r.uid, vis)

        self._test_on_each(test)

    def test_get_genotype_from_breeding(self):
        def test(x: Traitset):
            gen1 = x.get_random_genotype()
            gen2 = x.get_random_genotype()

            gen = x.get_genotype_from_breeding(gen1, gen2)
            for t in x.traits:
                self.assertIn(t.uid, gen)

        self._test_on_each(test)

    def test_derive_net_merit_from_genotype(self):
        def test(x: Traitset):
            gen = x.get_random_genotype()
            nm = x.derive_net_merit_from_genotype(gen)
            self.assertIsInstance(nm, float)

    def test_get_recessives_from_breeding(self):
        def test(x: Traitset):
            rec1 = x.get_random_recessives()
            rec2 = x.get_random_recessives()

            rec = x.get_recessives_from_breeding(rec1, rec2)
            for r in x.recessives:
                self.assertIn(r.uid, rec)

        self._test_on_each(test)

    def test_find_trait_or_null(self):
        def test(x: Traitset):
            for uid in x.traits:
                t = x.find_trait_or_null(uid)
                self.assertIsInstance(t, Trait)

            self.assertIsNone(x.find_trait_or_null(str(random())))

    def test_find_recessive_or_null(self):
        def test(x: Traitset):
            for uid in x.recessives:
                r = x.find_recessive_or_null(uid)
                self.assertIsInstance(r, Recessive)

            self.assertIsNone(x.find_recessive_or_null(str(random())))
