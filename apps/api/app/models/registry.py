"""Import every model module so ``Base.metadata`` describes the full schema.

Alembic, the schema audit and the drift check must see every table, not only the
ones imported transitively by whichever router happened to load first.
"""

from __future__ import annotations

import importlib
import pkgutil

import app.models as _models_pkg
from app.database import Base


def load_all_models():
    for mod in pkgutil.iter_modules(_models_pkg.__path__):
        if mod.name == "registry":
            continue
        importlib.import_module(f"{_models_pkg.__name__}.{mod.name}")
    return Base.metadata
