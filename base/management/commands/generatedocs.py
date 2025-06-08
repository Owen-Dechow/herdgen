import inspect
from pathlib import Path
from types import ModuleType
from typing import Callable
from django.db.models.query_utils import DeferredAttribute
from django.db.models.fields.related_descriptors import (
    ReverseManyToOneDescriptor,
)
from django.core.management.base import BaseCommand
import os
from inspect import getmodule, getsource

from herdgen.settings import BASE_DIR
from ... import models


MODELS_FILE = "models.md"
GENERATED_FILES = [MODELS_FILE]


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

    def document_class(self, klass: type) -> tuple[str, list]:
        classname = f"{klass.__name__}"

        if klass.__bases__:
            classname += (
                "(" + ".".join(x.__name__ for x in klass.__bases__) + ")"
            )

        output = []
        output.append(f"> {klass.__doc__}")

        fields = []
        functions = []
        classes = []

        parent_attrs = self.get_parent_attrs(klass)
        for field in klass.__dict__:
            if field not in parent_attrs:
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
                fields_list.append(
                    f"`{name}` {type_.__module__}.{type_.__name__}"
                )
            elif not isinstance(field, ReverseManyToOneDescriptor):
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

            try:
                source = ""
                trim = None
                for line in getsource(method).splitlines():
                    if trim is None:
                        source = line.lstrip()
                        trim = len(line) - len(source)
                        source += "\n"
                    else:
                        source += line[trim:] + "\n"

                method_list.append(f"```python\n{source}\n```")
            except TypeError:
                ...

        return (classname, output)

    def document_module(self, module: ModuleType) -> tuple[str, list]:
        output = []

        objs = self.get_direct_objects(module)
        for obj in objs:
            if isinstance(obj, type):
                output.append(self.document_class(obj))

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
        models_ = self.document_module(models)

        self.write_to_file(
            docs_folder / MODELS_FILE, self.convert_to_txt(models_)
        )

        self.stdout.write("Generating Documentation")
