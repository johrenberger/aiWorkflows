from __future__ import annotations

from pathlib import Path

__version__ = "0.1.0"

_SRC_PACKAGE = Path(__file__).resolve().parent.parent / "src" / "mutationctl"
if str(_SRC_PACKAGE) not in __path__:
    __path__.append(str(_SRC_PACKAGE))
