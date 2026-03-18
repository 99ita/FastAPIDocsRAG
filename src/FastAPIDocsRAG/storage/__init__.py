"""
Storage components for the ETVR system.
"""

from .base import StorageBackend
from .local import LocalStorage

__all__ = ["StorageBackend", "LocalStorage"]
