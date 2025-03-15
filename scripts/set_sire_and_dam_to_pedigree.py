from base.models import Animal


def set_sire_and_dam_to_pedigree():
    a = Animal.objects.defer(
        "name",
        "generation",
        "male",
        "genomic_tests",
        "genotype",
        "phenotype",
        "ptas",
        "recessives",
        "inbreeding",
        "net_merit",
    )

    animals = a.all()

    count = Animal.objects.count()
    print(f"{(count)} Animals to process")

    for idx, anim in enumerate(animals.iterator(chunk_size=50)):
        anim.sire = (
            a.get(id=anim.pedigree["sire"]["id"]) if anim.pedigree["sire"] else None
        )
        anim.dam = (
            a.get(id=anim.pedigree["dam"]["id"]) if anim.pedigree["dam"] else None
        )

        anim.save()
        print(f"Animal {idx + 1}/{count} {(idx - 1)/count * 100}%")
