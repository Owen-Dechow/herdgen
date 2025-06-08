# Adding Traitsets

1. To add a traitset you must add a traitset `json` file to the
`base/traitsets/traitsets/` folder.

2. Register the traitset in the `base/traitsets/__init__.py` file.

## 1. Adding the traitset file.

The traitset file must have the same name of the traitsets + `.json`.
For instance if I wanted to name a traitset `MY_TRAITSET`, the traitset
file name would be `MY_TRAITSET.json`. If a traitset fails to follow
this system it will not register properly.

Next place the traitset file into the `base/traitsets/traitsets/`
directory. In our example we would create a the file
`base/traitsets/traitsets/MY_TRAITSET.json`.

Within the traitset file you must define the traitset information.
The first thing we must add is a description. The description element
will be a string element with the key `"desc"`.

`base/traitsets/traitsets/MY_TRAITSET.json`
```json
{
    "desc": "An example traitset used for a tutorial"
}
```

The next element we must add are the traits. Traits are added to an
array with the key `"traits"`. Each trait is a single json object with
the following attributes:

1. `"uid"` -> A unique identifier (string)
2. `"heritability"` -> The genetic heritability/h^2 (float)
3. `"net_merit_dollars"`: -> The net merit dollars value (float)
4. `"inbreeding_depression_percentage"` -> % depression taken from
phenotype when multiplies by the inbreeding coefficient (float)
5. `"calculated_standard_deviation"` -> A standard deviation that the
above factors are scaled to (float)

Let us add two traits to our traitset.

`base/traitsets/traitsets/MY_TRAITSET.json`
```json
{
    "desc": ...
    "traits": [
        {
            "uid": "PL",
            "heritability": 0.08,
            "net_merit_dollars": 34,
            "inbreeding_depression_percentage": -0.28,
            "calculated_standard_deviation": 1.7
        },
        {
            "uid": "TY",
            "heritability": 0.25,
            "net_merit_dollars": 0,
            "inbreeding_depression_percentage": 0,
            "calculated_standard_deviation": 1
        }
    ]
}
```

For each trait that we create we must also add correlations to each 
other trait for genotypes and phenotypes. We do this by adding two
more elements to our traitset: `"genotype_correlations"` &
`"phenotype_correlations"`.

Both these elements will be two dimensional square arrays of the same
length as number of registered traits. The order in which the traits
are listed in `"traits"` corresponds to the index given to each trait
in the correlation array. These arrays represent the covariance
matrices. The major diagonal of the matrices should be all `1.00` as
each trait is 100% correlated to itself. The matrices must be square,
definite positive, & the same size as number of traits.

Now we can add out correlations to our example.

`base/traitsets/traitsets/MY_TRAITSET.json`
```json
{
    "traits": ...
    "genotype_correlations": [
        [ 1.00, -0.10],
        [-0.10,  1.00]
    ],
    "phenotype_correlations": [
        [ 1.00, -0.10],
        [-0.1,   1.00]
    ]
}
```

Although the genotype and phenotype correlations are the same in this
example they are not always 100% the same. See traitset
*ANIMAL_SCIENCE_422*.

The next element we must add are genetic recessives. We add genetic
recessives to an array with the key `"recessives"`. Each recessive
is then a json like object with the following attributes:

1. `"uid"` -> A unique identifier, UNIQUE ACROSS BOTH TRAITS AND
RECESSIVES (string)
2. `"fatal"` -> Tell if the recessive is fatal or not (bool)
3. `"prevalence_percent"` -> prevalence in initial population (float)

We can now add a recessive to our example.

`base/traitsets/traitsets/MY_TRAITSET.json`
```json
{
    "phenotype_correlations": ...
    "recessives": [
        {
            "uid": "CaR",
            "fatal": true,
            "prevalence_percent": 10
        }
    ]
}
```

The last thing we must do for our traitset file is register animals.
We must register at least one animal. Animals are registered in an
array like object with the key `"animals"`.

Each animal must define the following attributes:

1. `"herd"` -> The name for a group of animals (string)
2. `"male"` -> The name for an adult make (string)
3. `"female"` -> The name for an adult female (string)
4. `"sire"` -> The name for father (string)
5. `"dam"` -> The name for mother (string)
6. `"herds"` -> Plural for `"herd"` (string)
7. `"males"` -> Plural for `"male"` (string)
8. `"females"` -> Plural for `"female"` (string)
9. `"sires"` -> Plural for `"sire"` (string)
10. `"dams"` -> Plural for `"dam"` (string)
11. `"genotype_prefix"` -> The prefix used before genotypes,
12. typically "gen" (string)
13. `"phenotype_prefix"` -> The prefix used before phenotypes
14. typically "ph" (string)
15. `"pta_prefix"` -> The prefix used before PTAs
16. typically "PTA" or "EPD" (string)
17. `"traits"` -> Trait information for animal (json object)
18. `"recessives"` -> Recessive information for animal (json object)

For each trait you must add a json object under the key equivalent to
the trait's `"uid"`; that object must define the following attributes:

1. `"name"` -> The name of the trait (string)
2. `"standard_deviation"` -> Standard deviation for that trait for
animal (string)
3. `"phenotype_average"` -> Average phenotype for trait (float)
4. `"unit"` -> Unit for trait (string)

For each recessive you must add a json object under the key equivalent
to the recessive's `"uid"`; that object must define the following
attributes:

1. `"name"` -> Name of the recessive (string)

Now we may add the last elements to *MY_TRAITSET*.

`base/traitsets/traitsets/MY_TRAITSET.json`
```json
{
    "recessives": ...
    "animals": {
        "Bovine (Holstein)": {
        "herd": "herd",
        "male": "bull",
        "female": "cow",
        "sire": "sire",
        "dam": "dam",
        "herds": "herds",
        "males": "bulls",
        "females": "cows",
        "sires": "sires",
        "dams": "dams"
        "genotype_prefix": "gen",
        "phenotype_prefix": "ph",
        "pta_prefix": "pta",
            "traits": {
                "PL": {
                    "name": "Productive Life",
                    "standard_deviation": 1.7,
                    "phenotype_average": 5,
                    "unit": " years"
                },
                "TY": {
                    "name": "Type",
                    "standard_deviation": 1,
                    "phenotype_average": 0,
                    "unit": ""
                }
            },
            "recessives": {
                "CaR": {
                    "name": "Calf Recumbency"
                }
            },
        },
        "Dog": {
            "herd": "pack",
            "male": "stud",
            "female": "bitch",
            "sire": "sire",
            "dam": "dam",
            "herds": "packs",
            "males": "studs",
            "females": "bitches",
            "sires": "sires",
            "dams": "dams",
            "genotype_prefix": "gen",
            "phenotype_prefix": "ph",
            "pta_prefix": "pta",
            "traits": {
                "PL": {
                    "name": "Friendliness",
                    "standard_deviation": 1,
                    "phenotype_average": 2,
                    "unit": ""
                },
                "TY": {
                    "name": "Intelligence",
                    "standard_deviation": 1,
                    "phenotype_average": 2,
                    "unit": ""
                }
            },
            "recessives": {
                "CaR": {
                    "name": "Curly Tail"
                }
            }
        }
    }
}
```

The full example of our file will be as follows:

`base/traitsets/traitsets/MY_TRAITSET.json`
```json
{
    "desc": "An example traitset used for a tutorial",
    "traits": [
        {
            "uid": "PL",
            "heritability": 0.08,
            "net_merit_dollars": 34,
            "inbreeding_depression_percentage": -0.28,
            "calculated_standard_deviation": 1.7
        },
        {
            "uid": "TY",
            "heritability": 0.25,
            "net_merit_dollars": 0,
            "inbreeding_depression_percentage": 0,
            "calculated_standard_deviation": 1
        }
    ],
    "genotype_correlations": [
        [ 1.00, -0.10],
        [-0.10,  1.00]
    ],
    "phenotype_correlations": [
        [ 1.00, -0.10],
        [-0.1,   1.00]
    ],
    "recessives": [
        {
            "uid": "CaR",
            "fatal": true,
            "prevalence_percent": 10
        }
    ],
    "animals": {
        "Bovine (Holstein)": {
        "herd": "herd",
        "male": "bull",
        "female": "cow",
        "sire": "sire",
        "dam": "dam",
        "herds": "herds",
        "males": "bulls",
        "females": "cows",
        "sires": "sires",
        "dams": "dams"
        "genotype_prefix": "gen",
        "phenotype_prefix": "ph",
        "pta_prefix": "pta",
            "traits": {
                "PL": {
                    "name": "Productive Life",
                    "standard_deviation": 1.7,
                    "phenotype_average": 5,
                    "unit": " years"
                },
                "TY": {
                    "name": "Type",
                    "standard_deviation": 1,
                    "phenotype_average": 0,
                    "unit": ""
                }
            },
            "recessives": {
                "CaR": {
                    "name": "Calf Recumbency"
                }
            },
        },
        "Dog": {
            "herd": "pack",
            "male": "stud",
            "female": "bitch",
            "sire": "sire",
            "dam": "dam",
            "herds": "packs",
            "males": "studs",
            "females": "bitches",
            "sires": "sires",
            "dams": "dams",
            "genotype_prefix": "gen",
            "phenotype_prefix": "ph",
            "pta_prefix": "pta",
            "traits": {
                "PL": {
                    "name": "Friendliness",
                    "standard_deviation": 1,
                    "phenotype_average": 2,
                    "unit": ""
                },
                "TY": {
                    "name": "Intelligence",
                    "standard_deviation": 1,
                    "phenotype_average": 2,
                    "unit": ""
                }
            },
            "recessives": {
                "CaR": {
                    "name": "Curly Tail"
                }
            }
        }
    }
}
```

## 2. Registering the traitset

To register the traitset update the `REGISTERED` list in the
`base/traitsets/__init__.py` file. You must add a `Registration`
object to the list. The `Registration` default constructor takes
two arguments. The first is the name of the traitset that must match
the name of your traitset file - the `.json`. The second is a bool
wich tells of the traitset is active or not.

Lets add our example traitset to the registration.

`base/traitsets/__init__.py`
```python
...

REGISTERED = [
    Registration("ANIMAL_SCIENCE_422", True),
    Registration("MY_TRAITSET", True),
]
```

If the second value is `False` then the traitset is disabled and no
classes can be created with that traitset. YOU SHOULD NOT remove the
registration because older classes may still rely on it. Disabled
traitsets are not available for new classes but are still available
to any class that depends on it. If a class depends on a traitset that
had been removed from the registration instead as marked as disabled
then the simulation will yield undocumented and unpredictable results
and return errors.
