"""Controllo statico degli import, inclusi quelli nei blocchi TYPE_CHECKING."""
import ast
from importlib.util import resolve_name
from pathlib import Path
import sys

import pytest


PACKAGE = "local_document_search"
SOURCE = Path(__file__).resolve().parents[2] / "src" / PACKAGE


def import_violations(source: str, module: str, *, is_package: bool = False) -> list[str]:
    layer = module.split(".")[1]
    allowed_layers = {"domain"} if layer == "domain" else {"domain", "application"}
    package = module if is_package else module.rpartition(".")[0]
    violations = []
    for node in ast.walk(ast.parse(source)):
        dependencies = []
        if isinstance(node, ast.Import):
            dependencies = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            name = "." * node.level + (node.module or "")
            try:
                base = resolve_name(name, package) if node.level else name
            except (ImportError, ValueError):
                violations.append(name)
                continue
            dependencies = [base]
            # from package import infrastructure importa anche il sottomodulo.
            if base == PACKAGE:
                dependencies = [f"{base}.{alias.name}" for alias in node.names]
        for dependency in dependencies:
            parts = dependency.split(".")
            if parts[0] == PACKAGE:
                valid = len(parts) > 1 and parts[1] in allowed_layers
            else:
                valid = parts[0] in sys.stdlib_module_names and parts[0] != "sqlite3"
            if not valid:
                violations.append(dependency)
    return violations


def test_core_respects_dependency_boundaries():
    violations = {}
    for layer in ("domain", "application"):
        for path in (SOURCE / layer).rglob("*.py"):
            parts = path.relative_to(SOURCE.parent).with_suffix("").parts
            is_package = parts[-1] == "__init__"
            module = ".".join(parts[:-1] if is_package else parts)
            found = import_violations(path.read_text(encoding="utf-8"), module, is_package=is_package)
            if found:
                violations[str(path.relative_to(SOURCE))] = found
    assert violations == {}


@pytest.mark.parametrize("layer,source", [
    ("domain", "import local_document_search.application.contracts"),
    ("domain", "from ..application import contracts"),
    ("application", "from .. import infrastructure"),
    ("application", "from local_document_search import interfaces"),
    ("application", "from local_document_search.infrastructure import filesystem"),
    ("domain", "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    import pypdf"),
    ("application", "import PySide6.QtCore"),
    ("domain", "import sqlite3"),
    ("application", "from markdown_it import MarkdownIt"),
    ("domain", "from ... import outside"),
])
def test_checker_detects_forbidden_imports(layer, source):
    assert import_violations(source, f"{PACKAGE}.{layer}.example")


@pytest.mark.parametrize("layer,source", [
    ("domain", "from .documents import DocumentId"),
    ("domain", "from . import documents"),
    ("domain", "from dataclasses import dataclass"),
    ("application", "from ..domain.documents import DocumentId"),
    ("application", "from .ports import DocumentReaderPort"),
])
def test_checker_accepts_permitted_imports(layer, source):
    assert not import_violations(source, f"{PACKAGE}.{layer}.example")


def test_relative_import_in_package_initializer_is_resolved():
    assert import_violations("from .. import infrastructure", f"{PACKAGE}.domain", is_package=True)
    assert not import_violations("from . import documents", f"{PACKAGE}.domain", is_package=True)
