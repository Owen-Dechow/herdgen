from base.models import Class


def add_pta_visibility_defaults():
    classes = Class.objects.all()

    for klass in classes:
        for trait in klass.trait_visibility:
            if len(klass.trait_visibility[trait]) < 3:
                klass.trait_visibility[trait].append(True)

    Class.objects.bulk_update(classes, ["trait_visibility"])
