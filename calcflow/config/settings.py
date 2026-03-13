import os
import json

CONFIG_DIR = os.path.expanduser("~/.calcflow")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

_DEFAULT_CONFIG = {
    "cluster": {
        "scheduler": "sge",
        "default_queue": "long",
        "default_cores": 64,
        "parallel_env": "mpi-*",
        "vasp_module": "vasp/6.4.0/",
    },
    "vasp": {
        "default_executable": "vasp_std",
    },
}

_cached_config = None


def get_config():
    """Load config from ~/.calcflow/config.json, creating defaults if needed."""
    global _cached_config
    if _cached_config is not None:
        return _cached_config

    if not os.path.exists(CONFIG_FILE):
        write_default_config()

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        _cached_config = json.load(f)
    return _cached_config


def write_default_config():
    """Write default config file."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(_DEFAULT_CONFIG, f, indent=4)


def update_config(updates):
    """Merge updates into existing config and save."""
    config = get_config()
    for section, values in updates.items():
        if section in config and isinstance(config[section], dict):
            config[section].update(values)
        else:
            config[section] = values
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
    global _cached_config
    _cached_config = config
