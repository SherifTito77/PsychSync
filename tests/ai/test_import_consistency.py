import importlib
import os
import pkgutil
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import app


@pytest.mark.ai
def test_import_consistency():
    """Verify that all core AI/Clinical modules can be imported."""

    def iter_modules(package):
        for loader, name, is_pkg in pkgutil.walk_packages(
            package.__path__, package.__name__ + "."
        ):
            yield name
            if is_pkg:
                yield from iter_modules(importlib.import_module(name))

    for module_name in iter_modules(app):
        try:
            print(f"Importing {module_name}...")
            importlib.import_module(module_name)
        except ImportError as e:
            pytest.fail(f"Module {module_name} failed to import: {e}")
        except Exception as e:
            pytest.fail(f"Module {module_name} raised exception during import: {e}")
