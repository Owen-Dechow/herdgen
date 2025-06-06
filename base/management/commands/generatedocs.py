from pathlib import Path
from types import ModuleType
from typing import Callable
from django.core.management.base import BaseCommand
import shutil
import os
from inspect import getmodule
from herdgen.settings import BASE_DIR
from ... import models


class Command(BaseCommand):
    help = "Generate documentation for base."

    def reset_docs(self) -> Path:
        docs_folder = BASE_DIR / "docs"

        if docs_folder.exists():
            shutil.rmtree(docs_folder)

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
            output += f"(" + ".".join(x.__name__ for x in klass.__bases__) + ")"

        output += "\n"
        output += klass.__doc__ + "\n"

        parent_attrs = self.get_parent_attrs(klass)
        for field in klass.__dict__:
            if field not in parent_attrs:
                if field.__doc__.__len__() < 100:
                    print(field.__doc__)

        return output

    def document_module(self, module: ModuleType) -> str:
        output = f"# {module.__name__}\n"

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

        self.write_to_file(docs_folder / "models.md", models_)

        self.stdout.write("Generating Documentation")
