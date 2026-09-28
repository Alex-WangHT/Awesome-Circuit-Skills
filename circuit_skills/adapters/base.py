"""The stable interface for EDA-specific exporters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class EDAAdapter(ABC):
    @abstractmethod
    def export_component(self, ir: dict[str, Any], out_dir: Path) -> list[Path]:
        """Write symbol, footprint, and 3D library files."""

    @abstractmethod
    def export_architecture(self, ir: dict[str, Any], out_dir: Path) -> list[Path]:
        """Write graphical architecture artifacts, without electrical net claims."""
