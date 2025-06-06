from json import load
from pathlib import Path
from random import random
from typing import Callable, Optional, Type

from django.utils.html import SafeString
import numpy as np
from scipy.linalg import cholesky

wrap = lambda text, tag: f"<{tag}>\n    {text}\n</{tag}>"


def document(sig: str):
    def wrapper(func: Callable):
        func._is_serialized = True
        func._sig = sig
        return func

    return wrapper


def serializable_funcs(klass: Type):
    attrs = [getattr(klass, name, None) for name in dir(klass)]
    return [x for x in attrs if getattr(x, "_is_serialized", False)]


TRAITSET_PATH = Path(__file__).parent / "traitsets"

DESC_KEY = "desc"
TRAITS_KEY = "traits"
GENOTYPE_CORRELATIONS_KEY = "genotype_correlations"
PHENOTYPE_CORRELATIONS_KEY = "phenotype_correlations"
RECESSIVES_KEY = "recessives"
UID_KEY = "uid"
HERITABILITY_KEY = "heritability"
NET_MERIT_DOLLARS_KEY = "net_merit_dollars"
INBREEDING_DEPRESSION_PERCENTAGE_KEY = "inbreeding_depression_percentage"
PREVALENCE_PERCENT_KEY = "prevalence_percent"
FATAL_KEY = "fatal"
CALCULATED_STANDARD_DEVIATION_KEY = "calculated_standard_deviation"

PHENOTYPE_AVERAGE_KEY = "phenotype_average"
ANIMALS_KEY = "animals"
NAME_KEY = "name"
HERD_KEY = "herd"
MALE_KEY = "male"
FEMALE_KEY = "female"
SIRE_KEY = "sire"
DAM_KEY = "dam"
STANDARD_DEVIATION_KEY = "standard_deviation"
UNIT_KEY = "unit"

HERDS_KEY = "herds"
MALES_KEY = "males"
FEMALES_KEY = "females"
SIRES_KEY = "sires"
DAMS_KEY = "dams"

HETEROZYGOUS_KEY = "he"
HOMOZYGOUS_CARRIER_KEY = "ho(c)"
HOMOZYGOUS_FREE_KEY = "ho(f)"

PHENOTYPE_PREFIX_KEY = "phenotype_prefix"
GENOTYPE_PREFIX_KEY = "genotype_prefix"
PTA_PREFIX_KEY = "pta_prefix"


class RecessiveAnimalFilter:
    name: str

    def __init__(self, name: str):
        self.name = name


class TraitAnimalFilter:
    name: str
    standard_deviation: float
    phenotype_average: float
    unit: str

    def __init__(
        self,
        name: str,
        standard_deviation: float,
        phenotype_average: float,
        unit: str,
    ):
        self.name = name
        self.standard_deviation = standard_deviation
        self.phenotype_average = phenotype_average
        self.unit = unit


class TraitsetAnimalFilter:
    herd: str
    male: str
    female: str
    sire: str
    dam: str
    herds: str
    sires: str
    dams: str
    males: str
    females: str
    phenotype_prefix: str
    genotype_prefix: str
    pta_prefix: str

    def __init__(
        self,
        herd: str,
        male: str,
        female: str,
        sire: str,
        dam: str,
        herds: str,
        males: str,
        females: str,
        sires: str,
        dams: str,
        genotype_prefix: str,
        phenotype_prefix: str,
        pta_prefix: str,
    ):
        self.herd = herd
        self.male = male
        self.female = female
        self.herds = herds
        self.males = males
        self.females = females
        self.sire = sire
        self.dam = dam
        self.sires = sires
        self.dams = dams
        self.genotype_prefix = genotype_prefix
        self.phenotype_prefix = phenotype_prefix
        self.pta_prefix = pta_prefix


class Trait:
    uid: str
    heritability: float
    net_merit_dollars: float
    inbreeding_depression_percentage: float
    calculated_standard_deviation: float
    animals: dict[str, TraitAnimalFilter]

    def __init__(
        self,
        uid: str,
        heritability: float,
        net_merit_dollars: float,
        inbreeding_depression_percentage: float,
        calculated_standard_deviation: float,
        animals: dict[str, TraitAnimalFilter],
    ):
        self.uid = uid
        self.heritability = heritability
        self.net_merit_dollars = net_merit_dollars
        self.inbreeding_depression_percentage = inbreeding_depression_percentage
        self.calculated_standard_deviation = calculated_standard_deviation
        self.animals = animals

    @classmethod
    @document(
        """sqrt:
              x # any real number"""
    )
    def sqrt(cls, x: float) -> float:
        """# Yields the square root of x."""
        return np.sqrt(x)

    @classmethod
    @document(
        """limit:
              x # any real number
              max # maximum"""
    )
    def limit(cls, x: float, max: float) -> float:
        """# Yields the bounded value of x less than or equal to max."""
        return min(x, max)

    @classmethod
    @document(
        """nrandom:
              stdev # standard deviation"""
    )
    def mendelian_sample(cls, scale: float = 1) -> float:
        """# Yields a random value on a normal distribution."""
        return np.random.normal(scale=scale)

    @document(
        """convert_genotype_to_phenotype:
        gen # genotype
        stdev # standard deviation
        h2 # heritability
        inbc # inbreeding coefficient
        inbdp # inbreeding depression percentage"""
    )
    def convert_genotype_to_phenotype(
        self, genotype: float, inbreeding_coefficient: float
    ) -> float:
        """ph_v = (stdev**2) / h2
        res_v = ph_v * (1 - h2)
        res_stdev = sqrt(res_v)
        ph = gen * 2 + nrandom(res_std)
        phenotype = ph + inbc * 100 * inbdp"""

        genotype = genotype * self.calculated_standard_deviation

        phenotypic_variance = (
            self.calculated_standard_deviation**2
        ) / self.heritability
        residual_variance = phenotypic_variance * (1 - self.heritability)
        residual_standard_deviation = self.sqrt(residual_variance)
        phenotype = genotype * 2 + self.mendelian_sample(
            scale=residual_standard_deviation
        )

        phenotype += (
            inbreeding_coefficient * 100 * self.inbreeding_depression_percentage
        )

        return phenotype / self.calculated_standard_deviation

    @document(
        """convert_genotype_to_pta:
              gen # genotype
              nd # number of daughters
              ng # number of genomic tests
              stdev # standard deviation
              h2 # heritability"""
    )
    def convert_genotype_to_pta(
        self, genotype: float, number_of_daughters: int, genomic_tests: int, t=None
    ) -> float:
        """n = nd + ng * 2 * (1 / h2)
        k = (4 - h2) / h2
        urel = h2 + (n / (n + k))
        rel = limit(urel, 0.99)
        w1 = sqrt(rel)
        w2 = sqrt(1 - rel)
        noise = nrandom(stdev)
        PTA = ((w1 * gen + w2 * noise) * (rel^0.25)) / 2"""

        bv = genotype * self.calculated_standard_deviation

        n = number_of_daughters + genomic_tests * 2 * (1 / self.heritability)

        k = (4 - self.heritability) / self.heritability

        rel = self.heritability + (n / (n + k))

        rel = self.limit(rel, 0.99)

        w1 = self.sqrt(rel)

        w2 = self.sqrt(1 - rel)
        noise = self.mendelian_sample(self.calculated_standard_deviation)

        PTA = w1 * bv + w2 * noise
        PTA *= rel**0.25
        PTA /= 2

        return PTA / self.calculated_standard_deviation

    @document(
        """get_genotype_from_breeding:
              s_gen # sire genotype
              d_gen # dam genotype
              mds # mendelian sample"""
    )
    def get_genotype_from_breeding(
        self, sire_val: float, dam_val: float, mendelian_sample: float
    ) -> float:
        """sc = sqrt(2) / 2
        pa = (s_gen + d_gen) / 2
        scs = sc * mds
        genotype = pa + scs"""
        sire_val = sire_val * self.calculated_standard_deviation
        dam_val = dam_val * self.calculated_standard_deviation
        mendelian_sample = mendelian_sample * self.calculated_standard_deviation

        scale = self.sqrt(2) / 2
        parent_average = (sire_val + dam_val) / 2
        scaled_sample = scale * mendelian_sample
        result = parent_average + scaled_sample

        return result / self.calculated_standard_deviation

    @document(
        """get_net_merit_dollars_addend:
              gen # genotype
              nmd # net merit dollars"""
    )
    def get_net_merit_dollars_addend(self, genotype: float):
        """net_merit_dollars = gen * nmd"""
        genotype = genotype * self.calculated_standard_deviation
        return genotype * self.net_merit_dollars


class Recessive:
    uid: str
    fatal: bool
    prevalence_percent: float
    animals: dict[str, RecessiveAnimalFilter]

    def __init__(
        self,
        uid: str,
        fatal: bool,
        prevalence_percent: float,
        animals: dict[str, RecessiveAnimalFilter],
    ):
        self.uid = uid
        self.fatal = fatal
        self.prevalence_percent = prevalence_percent
        self.animals = animals

    @classmethod
    @document("""random""")
    def random(cls) -> float:
        """#Yields a random value in range [0, 1]"""
        return random()

    @document(
        """get_random:
              prev # prevalence percent"""
    )
    def get_random(self) -> str:
        """# [true, true], [true, false], or [false, false]
        alleles = [random() * 100 < prev, random() * 100 < prev]"""
        alleles = [self.random() * 100 < self.prevalence_percent for _ in range(2)]

        if all(alleles):
            return HOMOZYGOUS_CARRIER_KEY
        elif any(alleles):
            return HETEROZYGOUS_KEY
        else:
            return HOMOZYGOUS_FREE_KEY

    @classmethod
    @document(
        """get_passed_from_parent:
              p # parent gene"""
    )
    def get_passed_from_parent(cls, parent_allele) -> bool:
        """# Yields either first or second allele of p with equal weight."""
        if parent_allele == HOMOZYGOUS_CARRIER_KEY:
            return True
        elif parent_allele == HETEROZYGOUS_KEY:
            return cls.random() < 0.5
        else:
            return False

    @classmethod
    @document(
        """get_recessives_from_breeding:
              s # sire gene
              d # dam gene"""
    )
    def get_from_breeding(cls, sire_allele, dam_allele) -> str:
        """# [true, true], [true, false], or [false, false]
        alleles = [get_passed_from_parent(s), get_passed_from_parent(d)]"""
        alleles = [
            cls.get_passed_from_parent(sire_allele),
            cls.get_passed_from_parent(dam_allele),
        ]

        if all(alleles):
            return HOMOZYGOUS_CARRIER_KEY
        elif any(alleles):
            return HETEROZYGOUS_KEY
        else:
            return HOMOZYGOUS_FREE_KEY


class Traitset:
    name: str
    desc: str | None
    traits: list[Trait]
    recessives: list[Recessive]
    genotype_correlations: list[list[float]]
    phenotype_correlations: list[list[float]]
    animals: dict[str, TraitsetAnimalFilter]
    animal_choices: list[str]

    def __init__(self, name: str):
        self.name = name

        full_dict = self.get_dict()
        traits_list = full_dict[TRAITS_KEY]
        recessives_dict = full_dict[RECESSIVES_KEY]
        genotype_correlations_list = full_dict[GENOTYPE_CORRELATIONS_KEY]
        phenotype_correlations_list = full_dict[PHENOTYPE_CORRELATIONS_KEY]
        animals_dict = full_dict[ANIMALS_KEY]
        self.desc = full_dict.get(DESC_KEY, None)

        traits = [
            Trait(
                x[UID_KEY],
                x[HERITABILITY_KEY],
                x[NET_MERIT_DOLLARS_KEY],
                x[INBREEDING_DEPRESSION_PERCENTAGE_KEY],
                x[CALCULATED_STANDARD_DEVIATION_KEY],
                {
                    key: TraitAnimalFilter(
                        val[TRAITS_KEY][x[UID_KEY]][NAME_KEY],
                        val[TRAITS_KEY][x[UID_KEY]][STANDARD_DEVIATION_KEY],
                        val[TRAITS_KEY][x[UID_KEY]][PHENOTYPE_AVERAGE_KEY],
                        val[TRAITS_KEY][x[UID_KEY]][UNIT_KEY],
                    )
                    for key, val in animals_dict.items()
                },
            )
            for x in traits_list
        ]
        recessives = [
            Recessive(
                x[UID_KEY],
                x[FATAL_KEY],
                x[PREVALENCE_PERCENT_KEY],
                {
                    key: RecessiveAnimalFilter(
                        val[RECESSIVES_KEY][x[UID_KEY]][NAME_KEY],
                    )
                    for key, val in animals_dict.items()
                },
            )
            for x in recessives_dict
        ]

        self.traits = traits
        self.recessives = recessives
        self.genotype_correlations = genotype_correlations_list
        self.phenotype_correlations = phenotype_correlations_list
        self.animals = {
            x: TraitsetAnimalFilter(
                animals_dict[x][HERD_KEY],
                animals_dict[x][MALE_KEY],
                animals_dict[x][FEMALE_KEY],
                animals_dict[x][SIRE_KEY],
                animals_dict[x][DAM_KEY],
                animals_dict[x][HERDS_KEY],
                animals_dict[x][MALES_KEY],
                animals_dict[x][FEMALES_KEY],
                animals_dict[x][SIRES_KEY],
                animals_dict[x][DAMS_KEY],
                animals_dict[x][GENOTYPE_PREFIX_KEY],
                animals_dict[x][PHENOTYPE_PREFIX_KEY],
                animals_dict[x][PTA_PREFIX_KEY],
            )
            for x in animals_dict
        }

        self.animal_choices = [(x, x) for x in animals_dict]

    def get_default_trait_visibility(self) -> dict[str, list[bool]]:
        return {x.uid: [True, True, True] for x in self.traits}

    def get_default_recessive_visibility(self) -> dict[str, bool]:
        return {x.uid: True for x in self.recessives}

    @document("get_random_genotype")
    def get_random_genotype(self) -> dict[str, float]:
        """# Yields random set of values scaled to each traits standard deviation.
        # Correlates values using plotting over cholesky decomposition of
        #   genotype covariance matrix."""
        initial_values = np.array([Trait.mendelian_sample() for _ in self.traits])
        cholesky_decomposition = cholesky(np.array(self.genotype_correlations))
        correlated_values = np.dot(cholesky_decomposition, initial_values)

        return {
            trait.uid: val
            for trait, val in zip(self.traits, correlated_values, strict=True)
        }

    @document(
        """get_genotype_from_breeding:
              sg # sire genotype
              dg # dam genotype"""
    )
    def get_genotype_from_breeding(
        self, sire_genotype: dict[str, float], dam_genotype: dict[str, float]
    ) -> dict[str, float]:
        """# Gets correlated mendealian samples using get_random_genotype function.
        # Finalizes genotype value using get_genotype_from_breeding
        #   function of each trait."""
        mendealian_sample = self.get_random_genotype()
        genotype = {
            x.uid: x.get_genotype_from_breeding(
                sire_genotype[x.uid],
                dam_genotype[x.uid],
                mendealian_sample[x.uid],
            )
            for x in self.traits
        }

        return genotype

    @document(
        """derive_phenotype_from_genotype:
              gen # genotype
              inbc # inbreeding coefficient"""
    )
    def derive_phenotype_from_genotype(
        self,
        genotype: dict[str, float],
        inbreeding_coefficient: float,
    ) -> dict[str, float]:
        """# Gets phenotypes from each trait's convert_genotype_to_phenotype function.
        # Correlates using cholesky decomposition of phenotype covariance matrix."""
        initial_values = np.array(
            [
                x.convert_genotype_to_phenotype(genotype[x.uid], inbreeding_coefficient)
                for x in self.traits
            ]
        )
        cholesky_decomposition = cholesky(np.array(self.phenotype_correlations))
        correlated_values = np.dot(cholesky_decomposition, initial_values)

        return {
            trait.uid: val
            for trait, val in zip(self.traits, correlated_values, strict=True)
        }

    def get_null_phenotype(self) -> dict[str, None]:
        return {x.uid: None for x in self.traits}

    @document(
        """derive_ptas_from_genotype:
              gen # genotype
              nd # number of daughters
              ng # number of genomic tests"""
    )
    def derive_ptas_from_genotype(
        self, genotype: dict[str, float], number_of_daughters: int, genomic_tests: int
    ) -> dict[str, float]:
        """# Gets PTA from each trait's convert_genotype_to_pta function."""
        return {
            key: self.find_trait_or_null(key).convert_genotype_to_pta(
                val, number_of_daughters, genomic_tests, t=key
            )
            for key, val in genotype.items()
        }

    def derive_net_merit_from_genotype(self, genotype: dict[str, float]) -> float:
        net_merit = 0
        for trait in self.traits:
            net_merit += trait.get_net_merit_dollars_addend(genotype[trait.uid])

        return net_merit

    def get_random_recessives(self) -> dict[str, str]:
        return {x.uid: x.get_random() for x in self.recessives}

    def get_recessives_from_breeding(
        self, sire_recessives: dict[str, str], dam_recessives: dict[str, str]
    ) -> dict[str, str]:
        recessives = {
            x.uid: Recessive.get_from_breeding(
                sire_recessives[x.uid], dam_recessives[x.uid]
            )
            for x in self.recessives
        }
        return recessives

    def find_trait_or_null(self, trait: str) -> Optional[Trait]:
        for t in self.traits:
            if t.uid == trait:
                return t

        return None

    def find_recessive_or_null(self, recessive: str) -> Optional[Recessive]:
        for r in self.recessives:
            if r.uid == recessive:
                return r

        return None

    def get_dict(self) -> dict[str, str | float | dict]:
        return load(open(TRAITSET_PATH / f"{self.name}.json", "r"))

    def get_html_animal_table(self) -> SafeString:
        headers = wrap("Animal", "th")
        headers += wrap("Sire", "th")
        headers += wrap("Dam", "th")
        headers += wrap("Male", "th")
        headers += wrap("Female", "th")
        headers += wrap("Herd", "th")
        headers += wrap("Genotype Prefix", "th")
        headers += wrap("Phenotype Prefix", "th")
        headers += wrap("PTA Prefix", "th")

        rows = wrap(headers, "tr")

        for key, animal in self.animals.items():
            row = wrap(key, "td")
            row += wrap(animal.sire, "td")
            row += wrap(animal.dam, "td")
            row += wrap(animal.male, "td")
            row += wrap(animal.female, "td")
            row += wrap(animal.herd, "td")
            row += wrap(animal.genotype_prefix, "td")
            row += wrap(animal.phenotype_prefix, "td")
            row += wrap(animal.pta_prefix, "td")

            rows += wrap(row, "tr")

        return SafeString(rows)

    def get_html_animal_recessive_table(self) -> SafeString:
        headers = wrap("Animal", "th")

        for recessive in self.recessives:
            headers += wrap(recessive.uid, "th")
        rows = wrap(headers, "tr")

        for animal in self.animals:
            row = wrap(animal, "td")

            for recessive in self.recessives:
                row += wrap(recessive.animals[animal].name, "td")

            rows += wrap(row, "tr")

        return SafeString(rows)

    def get_html_animal_trait_table(self) -> SafeString:
        headers = wrap("Animal", "th")
        for trait in self.traits:
            headers += wrap(trait.uid, "th")
        rows = wrap(headers, "tr")

        for animal in self.animals:
            row = wrap(animal, "td")
            for trait in self.traits:
                filter = trait.animals[animal]
                cell = f"name: {filter.name}<br>"
                cell += f"mean: {filter.phenotype_average}<br>"
                cell += f"stdev: {filter.standard_deviation}<br>"
                cell += f"unit: {filter.unit or "~"}"

                row += wrap(cell, "td")

            rows += wrap(row, "tr")

        return SafeString(rows)

    def get_html_trait_table(self) -> SafeString:
        headers = wrap("Trait", "th")
        headers += wrap("Base Standard Deviation", "th")
        headers += wrap("Heritability", "th")
        headers += wrap("Inbreeding Depression Percentage", "th")
        headers += wrap("Net Merit Dollars", "th")

        rows = wrap(headers, "tr")

        for trait in self.traits:
            row = wrap(trait.uid, "td")
            row += wrap(trait.calculated_standard_deviation, "td")
            row += wrap(trait.heritability, "td")
            row += wrap(trait.inbreeding_depression_percentage, "td")
            row += wrap(trait.net_merit_dollars, "td")
            rows += wrap(row, "tr")

        return SafeString(rows)

    def get_html_recessive_table(self) -> SafeString:
        headers = wrap("Recessive", "th")
        headers += wrap("Prevalence Percentage", "th")
        headers += wrap("Fatal", "th")

        rows = wrap(headers, "tr")

        for recessive in self.recessives:
            row = wrap(recessive.uid, "td")
            row += wrap(recessive.prevalence_percent, "td")
            row += wrap(recessive.fatal, "td")

            rows += wrap(row, "tr")

        return SafeString(rows)

    def get_html_genotype_correlation_table(self) -> SafeString:
        return self.get_html_correlation_table(self.genotype_correlations)

    def get_html_phenotype_correlation_table(self) -> SafeString:
        return self.get_html_correlation_table(self.phenotype_correlations)

    def get_html_correlation_table(self, correlations: list[list[float]]) -> SafeString:
        headers = wrap("", "th")

        for trait in self.traits:
            headers += wrap(trait.uid, "th")

        rows = wrap(headers, "tr")

        for trait_idx, corr_row in enumerate(correlations):
            row = wrap(self.traits[trait_idx].uid, "th")

            for value in corr_row:
                row += wrap(value, "td")

            rows += wrap(row, "tr")

        return SafeString(rows)


DOCUMENTED_FUNCS = {
    "Per Trait Equations": serializable_funcs(Trait),
    "Cross Trait Equations": serializable_funcs(Traitset),
    "Per Recessive Equations": serializable_funcs(Recessive),
}
