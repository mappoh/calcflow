import os
import json
import shutil
from importlib import resources

from calcflow import PresetNotFoundError

USER_PRESETS_DIR = os.path.expanduser("~/.calcflow/presets")

_BUILTIN_PRESETS_DIR = str(resources.files("calcflow") / "data" / "presets")


def _builtin_presets_dir():
    """Path to built-in presets shipped with the package."""
    return _BUILTIN_PRESETS_DIR


def init_user_presets():
    """Copy built-in presets to user directory if they don't already exist.

    This ensures users always have editable copies of the default presets
    at ~/.calcflow/presets/. Existing user presets are never overwritten.
    """
    builtin_dir = _builtin_presets_dir()
    if not os.path.isdir(builtin_dir):
        return
    os.makedirs(USER_PRESETS_DIR, exist_ok=True)
    for fname in os.listdir(builtin_dir):
        if not fname.endswith(".json"):
            continue
        dest = os.path.join(USER_PRESETS_DIR, fname)
        if not os.path.exists(dest):
            shutil.copy2(os.path.join(builtin_dir, fname), dest)


def load_preset(name):
    """Load a named INCAR preset from user directory, falling back to built-ins."""
    for directory in (USER_PRESETS_DIR, _builtin_presets_dir()):
        path = os.path.join(directory, f"{name}.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            continue

    raise PresetNotFoundError(f"Preset '{name}' not found.")


def list_presets():
    """Return names of all available presets (user + builtin, deduplicated)."""
    names = set()

    builtin_dir = _builtin_presets_dir()
    if os.path.isdir(builtin_dir):
        for f in os.listdir(builtin_dir):
            if f.endswith(".json"):
                names.add(f[:-5])

    if os.path.isdir(USER_PRESETS_DIR):
        for f in os.listdir(USER_PRESETS_DIR):
            if f.endswith(".json"):
                names.add(f[:-5])

    return sorted(names)


def merge_preset(name, overrides):
    """Load a preset and apply key-level overrides without mutating the stored file."""
    params = load_preset(name)
    params.update(overrides)
    return params


def save_user_preset(name, params):
    """Save a preset to the user's preset directory."""
    os.makedirs(USER_PRESETS_DIR, exist_ok=True)
    path = os.path.join(USER_PRESETS_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(params, f, indent=4)
    return path
