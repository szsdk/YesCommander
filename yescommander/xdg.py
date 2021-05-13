import os
from pathlib import Path

__all__ = ["config_path", "cache_path"]


def _get_path(var, folder) -> Path:
    value = os.environ.get(var)
    if value and os.path.isabs(value):
        return Path(value) / "yescommander"
    return Path.home() / folder / "yescommander"


config_path = _get_path("XDG_CONFIG_DIRS", ".config")
cache_path = _get_path("XDG_CACHE_DIRS", ".cache")
