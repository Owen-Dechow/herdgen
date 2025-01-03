from json import load
from pathlib import Path
from random import random
from typing import Optional
import numpy as np
from scipy.linalg import cholesky


TRAITSET_PATH = Path(__file__).parent / "traitsets"

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
    def mendelian_sample(cls, scale: float = 1) -> float:
        return np.random.normal(scale=scale)

    def convert_genotype_to_phenotype(
        self, genotype: float, inbreeding_coefficient: float
    ) -> float:
        genotype = genotype * self.calculated_standard_deviation

        phenotypic_variance = (self.calculated_standard_deviation**2) / self.heritability
        residual_variance = phenotypic_variance * (1 - self.heritability)
        residual_standard_deviation = np.sqrt(residual_variance)
        phenotype = genotype * 2 + self.mendelian_sample(
            scale=residual_standard_deviation
        )

        phenotype += inbreeding_coefficient * 100 * self.inbreeding_depression_percentage

        return phenotype / self.calculated_standard_deviation

    def convert_genotype_to_pta(
        self, genotype: float, number_of_daughters: int, genomic_tests: int
    ) -> float:
        n = number_of_daughters + genomic_tests * 2 * (1 / self.heritability)

        bv = genotype * self.calculated_standard_deviation

        k = (4 - self.heritability) / self.heritability

        rel = self.heritability + (n / (n + k))
        rel = min(rel, 0.99)

        w1 = np.sqrt(rel)
        w2 = np.sqrt(1 - rel)

        noise = self.mendelian_sample(self.calculated_standard_deviation)
        PTA = w1 * bv + w2 * noise
        PTA *= rel
        PTA /= 2

        return PTA / self.calculated_standard_deviation

    def get_from_breeding(
        self, sire_val: float, dam_val: float, mendelian_sample: float
    ) -> float:
        sire_val = sire_val * self.calculated_standard_deviation
        dam_val = dam_val * self.calculated_standard_deviation
        mendelian_sample = mendelian_sample * self.calculated_standard_deviation

        scale = np.sqrt(2) / 2
        parent_average = (sire_val + dam_val) / 2
        scaled_sample = scale * mendelian_sample
        result = parent_average + scaled_sample

        return result / self.calculated_standard_deviation

    def get_net_merit_dollars(self, genotype: float):
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

    def get_random(self) -> str:
        alleles = [random() * 100 < self.prevalence_percent for _ in range(2)]

        if all(alleles):
            return HOMOZYGOUS_CARRIER_KEY
        elif any(alleles):
            return HETEROZYGOUS_KEY
        else:
            return HOMOZYGOUS_FREE_KEY

    @classmethod
    def get_passed_from_parent(cls, parent_allele):
        if parent_allele == HOMOZYGOUS_CARRIER_KEY:
            return True
        elif parent_allele == HETEROZYGOUS_KEY:
            return random() < 0.5
        else:
            return False

    @classmethod
    def get_from_breeding(cls, sire_allele, dam_allele) -> str:
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
    traits: list[Trait]
    recessives: list[Recessive]
    genotype_correlations: list[list[float]]
    phenotype_correlations: list[list[float]]
    animals: dict[str, TraitsetAnimalFilter]
    animal_choices: list[str]

    def __init__(self, name: str):
        self.name = name

        full_dict = load(open(TRAITSET_PATH / f"{name}.json", "r"))
        traits_list = full_dict[TRAITS_KEY]
        recessives_dict = full_dict[RECESSIVES_KEY]
        genotype_correlations_list = full_dict[GENOTYPE_CORRELATIONS_KEY]
        phenotype_correlations_list = full_dict[PHENOTYPE_CORRELATIONS_KEY]
        animals_dict = full_dict[ANIMALS_KEY]

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

    def get_random_genotype(self) -> dict[str, float]:
        initial_values = np.array([Trait.mendelian_sample() for _ in self.traits])
        cholesky_decomposition = cholesky(np.array(self.genotype_correlations))
        correlated_values = np.dot(cholesky_decomposition, initial_values)

        return {
            trait.uid: val
            for trait, val in zip(self.traits, correlated_values, strict=True)
        }

    def get_genotype_from_breeding(
        self, sire_genotype: dict[str, float], dam_genotype: dict[str, float]
    ) -> dict[str, float]:
        mendealian_sample = self.get_random_genotype()
        genotype = {
            x.uid: x.get_from_breeding(
                sire_genotype[x.uid],
                dam_genotype[x.uid],
                mendealian_sample[x.uid],
            )
            for x in self.traits
        }

        return genotype

    def derive_phenotype_from_genotype(
        self,
        genotype: dict[str, float],
        inbreeding_coefficient: float,
    ) -> dict[str, float]:
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

    def derive_ptas_from_genotype(
        self, genotype: dict[str, float], number_of_daughters: int, genomic_tests: int
    ) -> dict[str, float]:
        return {
            key: self.find_trait_or_null(key).convert_genotype_to_pta(
                val, number_of_daughters, genomic_tests
            )
            for key, val in genotype.items()
        }

    def derive_net_merit_from_genotype(self, genotype: dict[str, float]) -> float:
        net_merit = 0
        for trait in self.traits:
            net_merit += trait.get_net_merit_dollars(genotype[trait.uid])

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
