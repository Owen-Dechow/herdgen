import inspect
from pathlib import Path
from types import ModuleType
from typing import Callable
from django.db.models.query_utils import DeferredAttribute
from django.db.models.fields.related_descriptors import ReverseManyToOneDescriptor
from django.core.management.base import BaseCommand
import os
from inspect import getmodule

from six import class_types
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

    def document_class(self, klass: type) -> str:
        output = f"## {klass.__name__}"

        if klass.__bases__:
            output += "(" + ".".join(x.__name__ for x in klass.__bases__) + ")"

        output += "\n"
        output += klass.__doc__ + "\n\n"

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

        output += "### Fields\n"

        for name, field in fields:
            if isinstance(field, DeferredAttribute):
                type_ = type(klass._meta.get_field(name))
                output += f"`{name}` {type_.__module__}.{type_.__name__}\n\n"
            elif not isinstance(field, ReverseManyToOneDescriptor):
                output += f"`{name}` {type(field).__module__}.{type(field).__name__}\n\n"

        output += "### Methods\n"

        for name, method in functions:
            output += f"`{name}{inspect.signature(getattr(klass, name))}` {
                type(method).__module__
            }.{type(method).__name__}\n\n"
            if method.__doc__:
                output += method.__doc__ + "\n\n"

        return output

    def document_module(self, module: ModuleType) -> str:
        output = f"# {module.__name__}\n\n"

        objs = self.get_direct_objects(module)
        for obj in objs:
            if isinstance(obj, type):
                output += self.document_class(obj)

        return output

    def write_to_file(self, path: Path, contents: str):
        with open(path, "w") as file:
            file.write(contents)

    def handle(self, *args, **kwargs):
        docs_folder = self.reset_docs()
        models_ = self.document_module(models)

        self.write_to_file(docs_folder / MODELS_FILE, models_)

        self.stdout.write("Generating Documentation")
