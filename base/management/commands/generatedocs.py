import inspect
import os
from inspect import getmodule, getsource
from pathlib import Path
from types import ModuleType
from typing import Callable

from django.core.management.base import BaseCommand
from django.db.models import Model
from django.db.models.fields.related import ForeignKey
from django.db.models.fields.related_descriptors import (
    ForwardManyToOneDescriptor,
    ReverseManyToOneDescriptor,
)
from django.db.models.query_utils import DeferredAttribute

from herdgen.settings import BASE_DIR

from ... import models, forms, csv, inbreeding, names, views, views_utils

MODELS_FILE = "models.md"
FORMS_FILE = "forms.md"
CSV_FILE = "csv.md"
INBREEDING_FILE = "inbreeding.md"
NAMES_FILE = "names.md"
VIEWS_FILE = "views.md"
VIEWS_UTILS_FILES = "views_utils.md"

GENERATED_FILES = [MODELS_FILE, FORMS_FILE]


class Command(BaseCommand):
    help = "Generate documentation for base."

    def reset_docs(self) -> Path:
        docs_folder = BASE_DIR / "docs"

        if docs_folder.exists():
            for file in GENERATED_FILES:
                if (docs_folder / file).exists():
                    os.remove(docs_folder / file)
        else:
            os.mkdir(docs_folder)

        return docs_folder

    def get_direct_objects(self, module: ModuleType) -> list[type | Callable]:
        contents = []

        for var in vars(module):
            obj = module.__getattribute__(var)
            mod = getmodule(obj)
            if mod:
                mod = mod.__name__
            else:
                None

            if mod == module.__name__:
                contents.append(obj)

        return contents

    def get_parent_attrs(self, klass: type) -> set[str]:
        attrs = set()

        for base in klass.__bases__:
            if base == models.models.Model:
                attrs |= {
                    "id",
                    "objects",
                    "_meta",
                    "DoesNotExist",
                    "MultipleObjectsReturned",
                }

            for attr in vars(base):
                attrs.add(attr)

        return attrs

    def document_class(self, klass: type, mod_classes: list[type]) -> tuple[str, list]:
        classname = f"{klass.__name__}"

        output = [f"> {klass.__doc__}"]

        if klass.__bases__:
            output.append(
                (
                    "Bases",
                    [f"* {x.__module__}.{x.__name__}" for x in klass.__bases__],
                )
            )

        fields = []
        functions = []
        classes = []

        for field in klass.__dict__:
            if field in [
                "__module__",
                "__firstlineno__",
                "__doc__",
                "__static_attributes__",
                "_meta",
                "__str__",
            ]:
                continue

            if Model in klass.__bases__ and field in ["objects"]:
                continue

            obj = klass.__dict__[field]
            if isinstance(obj, type):
                classes.append((field, obj))
            elif callable(obj) or isinstance(obj, classmethod):
                functions.append((field, obj))
            else:
                fields.append((field, obj))

        fields_list = []
        output.append(("Fields", fields_list))

        for name, field in fields:
            if isinstance(field, DeferredAttribute):
                type_ = type(klass._meta.get_field(name))

                module = (
                    type_.__module__.removesuffix("related")
                    .removesuffix(".")
                    .removesuffix("json")
                    .removesuffix(".")
                    .removesuffix("fields")
                )
                type_name = type_.__name__
                type_str = module + type_name
                link = (
                    "https://docs.djangoproject.com/en/5.2/ref/models/fields/#"
                    + type_str
                )

                fields_list.append(f"`{name}` [{type_str}]({link})")

                if type_ is ForeignKey:
                    rel = klass._meta.get_field(name).related_model

                    if rel in mod_classes:
                        fields_list[-1] += (
                            " to ["
                            + rel.__module__
                            + "."
                            + rel.__name__
                            + "]"
                            + f"(#{rel.__name__.lower()})"
                        )
                    else:
                        fields_list[-1] += " to " + rel.__module__ + "." + rel.__name__

            elif not isinstance(
                field, (ReverseManyToOneDescriptor, ForwardManyToOneDescriptor)
            ):
                fields_list.append(
                    f"`{name}` {type(field).__module__}.{type(field).__name__}"
                )

        method_list = []
        output.append(("Methods", method_list))

        for name, method in functions:
            method_list.append(
                f"`{name}{inspect.signature(getattr(klass, name))}` {
                    type(method).__module__
                }.{type(method).__name__}"
            )
            if method.__doc__:
                method_list.append(f"> {method.__doc__}")

        output.append(("Source", [f"```python\n{getsource(klass)}\n```"]))

        return (classname, output)

    def document_module(self, module: ModuleType) -> tuple[str, list]:
        output = []

        objs = self.get_direct_objects(module)
        classes = []

        for obj in objs:
            if isinstance(obj, type):
                classes.append(obj)

        for obj in classes:
            output.append(self.document_class(obj, classes))

        return (f"{module.__name__}", output)

    def write_to_file(self, path: Path, contents: str):
        with open(path, "w") as file:
            file.write(contents)

    def convert_to_txt(self, data: tuple[str, list], layer=1) -> str:
        pad = "#" * layer + " "
        output = pad + data[0] + "\n"
        layer += 1
        pad += "| "
        pad = ""

        for obj in data[1]:
            if isinstance(obj, tuple):
                output += self.convert_to_txt(obj, layer)
            else:
                if "\n" in obj:
                    for line in obj.split("\n"):
                        output += pad + line + "\n"
                    output += "\n"
                else:
                    output += pad + obj + "\n\n"

        return output

    def handle(self, *args, **kwargs):
        docs_folder = self.reset_docs()

        self.write_to_file(
            docs_folder / MODELS_FILE,
            self.convert_to_txt(self.document_module(models)),
        )

        self.write_to_file(
            docs_folder / FORMS_FILE,
            self.convert_to_txt(self.document_module(forms)),
        )

        self.write_to_file(
            docs_folder / CSV_FILE,
            self.convert_to_txt(self.document_module(csv)),
        )

        self.write_to_file(
            docs_folder / INBREEDING_FILE,
            self.convert_to_txt(self.document_module(inbreeding)),
        )

        self.write_to_file(
            docs_folder / NAMES_FILE,
            self.convert_to_txt(self.document_module(names)),
        )

        self.write_to_file(
            docs_folder / VIEWS_FILE,
            self.convert_to_txt(self.document_module(views)),
        )

        self.write_to_file(
            docs_folder / VIEWS_UTILS_FILES,
            self.convert_to_txt(self.document_module(views_utils)),
        )

        self.stdout.write("Generating Documentation")
