"""
Validation-mode settings registry.

Controls what happens when a Quercus export is missing required columns:

    "warn"   -> proceed with the export; missing columns are added as empty
                columns and the response carries an X-Missing-Required header.
    "strict" -> reject the export with a structured 422 (original behavior).

Resolution order (highest precedence first):
    1. Environment variable  VALIDATION_MODE_<SYSTEM>  (e.g. VALIDATION_MODE_LDAP)
    2. settings.json file   (managed via the /admin/settings API)
    3. Default              (per-system: "ldap" defaults to "strict", all
                             other systems default to "warn")

The ldap default is strict deliberately: the LDAP admin's requirement (email
from John O Donnell, 2026-08-13) is that a missing required column must block
the export rather than go out blank — a DOB column present with empty cells is
fine, but a missing column is rejected. Other systems default to warn until a
similar decision is made for them.

The settings file lives at app/core/settings.json by default (path overridable
with the NCAD_SETTINGS_FILE env var) and is gitignored — it is per-deployment
state and resets when the backend is redeployed without an env override.

Structured as a small generic registry so future settings can slot in
alongside "validation_modes" without new plumbing.
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

VALID_SYSTEMS = ("ldap", "canvas", "google", "athens", "library")
VALID_MODES = ("warn", "strict")
DEFAULT_MODE = "warn"
DEFAULT_MODES = {
    "ldap": "strict",
    "canvas": "warn",
    "google": "warn",
    "athens": "warn",
    "library": "warn",
}

_SETTINGS_FILE_ENV = "NCAD_SETTINGS_FILE"
_DEFAULT_SETTINGS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "settings.json"
)
_SYSTEM_ENV_PREFIX = "VALIDATION_MODE_"


def _default_modes() -> dict[str, str]:
    return dict(DEFAULT_MODES)


def _settings_path() -> str:
    return os.environ.get(_SETTINGS_FILE_ENV, _DEFAULT_SETTINGS_PATH)


def _coerce_modes(raw: dict) -> dict[str, str]:
    modes: dict[str, str] = {}
    for system, mode in raw.items():
        if system in VALID_SYSTEMS and str(mode).strip() in VALID_MODES:
            modes[system] = str(mode).strip()
    return modes


def _read_file_modes() -> dict[str, str]:
    try:
        with open(_settings_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        return _coerce_modes(data.get("validation_modes", {}))
    except FileNotFoundError:
        return {}
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to read settings file: %s", e)
        return {}


def _env_modes() -> dict[str, str]:
    modes: dict[str, str] = {}
    for system in VALID_SYSTEMS:
        value = os.environ.get(_SYSTEM_ENV_PREFIX + system.upper())
        if value and value.strip() in VALID_MODES:
            modes[system] = value.strip()
    return modes


def get_validation_mode(system: str) -> str:
    """Effective validation mode for a system: env -> settings file -> default."""
    if system not in VALID_SYSTEMS:
        return DEFAULT_MODE
    env_modes = _env_modes()
    if system in env_modes:
        return env_modes[system]
    return _read_file_modes().get(system, DEFAULT_MODES.get(system, DEFAULT_MODE))


def get_all_validation_modes() -> dict[str, str]:
    modes = _default_modes()
    file_modes = _read_file_modes()
    env_modes = _env_modes()
    for system in VALID_SYSTEMS:
        modes[system] = env_modes.get(system, file_modes.get(system, modes[system]))
    return modes


def set_validation_mode(system: str, mode: str) -> dict[str, str]:
    """Persist a mode to the settings file. Env vars still take precedence."""
    if system not in VALID_SYSTEMS:
        raise ValueError(f"Unknown system: {system}")
    if mode not in VALID_MODES:
        raise ValueError(f"Invalid mode: {mode} (expected one of {VALID_MODES})")

    modes = _read_file_modes()
    modes[system] = mode
    data = {"validation_modes": modes}
    path = _settings_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    os.replace(tmp_path, path)
    return get_all_validation_modes()


def source_of(system: str) -> str:
    """Where the effective mode comes from ('env', 'file', or 'default')."""
    if system not in VALID_SYSTEMS:
        return "default"
    if system in _env_modes():
        return "env"
    if system in _read_file_modes():
        return "file"
    return "default"
