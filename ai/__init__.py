"""Compatibility package for legacy `ai.*` imports.

This project moved the canonical implementation under `app/ai`, but a large
test and service surface still imports modules from the top-level `ai`
namespace. Extending the package path keeps those imports working without
duplicating code.
"""

from pathlib import Path
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)  # type: ignore[name-defined]

_repo_root = Path(__file__).resolve().parent.parent
_app_ai = _repo_root / "app" / "ai"
if _app_ai.exists():
    __path__.append(str(_app_ai))
