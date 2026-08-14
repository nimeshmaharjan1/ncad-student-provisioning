"""
Unit tests for the validation-mode settings registry (app/core/settings.py).

Run from the backend/ directory:
    .venv\\Scripts\\python.exe samples\\test_settings.py

Covers:
  - Per-system defaults (ldap -> strict, everything else -> warn).
  - File persistence roundtrip (set_validation_mode -> settings.json -> read back).
  - Env var override takes precedence over the settings file.
  - Invalid systems/modes are rejected.
  - source_of() reports where the effective mode comes from.
  - A missing/corrupt settings file degrades to defaults.
"""

import json
import os
import sys
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import app.core.settings as settings

PASS = 0
FAIL = 0


def check(name: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}  {detail}")


def main():
    print("== Validation settings registry ==")

    tmp_dir = tempfile.mkdtemp(prefix="ncad_settings_")
    tmp_file = os.path.join(tmp_dir, "settings.json")

    old_env_file = os.environ.get("NCAD_SETTINGS_FILE")
    os.environ["NCAD_SETTINGS_FILE"] = tmp_file
    for system in settings.VALID_SYSTEMS:
        os.environ.pop(f"VALIDATION_MODE_{system.upper()}", None)

    try:
        # 1. Defaults
        print("Defaults:")
        for system in settings.VALID_SYSTEMS:
            check(
                f"default {system} is {settings.DEFAULT_MODES[system]}",
                settings.get_validation_mode(system) == settings.DEFAULT_MODES[system],
            )
        check("ldap defaults to strict", settings.get_validation_mode("ldap") == "strict")
        check("others default to warn", settings.get_validation_mode("canvas") == "warn")
        check("source_of default", settings.source_of("ldap") == "default")

        # 2. File persistence roundtrip
        print("File persistence:")
        modes = settings.set_validation_mode("ldap", "strict")
        check("set_validation_mode returns strict ldap", modes["ldap"] == "strict")
        check("get_validation_mode reads back strict", settings.get_validation_mode("ldap") == "strict")
        check("source_of file", settings.source_of("ldap") == "file")
        with open(tmp_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        check("settings.json written correctly", data.get("validation_modes", {}).get("ldap") == "strict")
        check("other systems untouched", settings.get_validation_mode("canvas") == "warn")

        # 3. Env override beats file
        print("Env override:")
        os.environ["VALIDATION_MODE_LDAP"] = "warn"
        check("env overrides file", settings.get_validation_mode("ldap") == "warn")
        check("source_of env", settings.source_of("ldap") == "env")
        os.environ["VALIDATION_MODE_CANVAS"] = "strict"
        check("env applies to other systems", settings.get_validation_mode("canvas") == "strict")

        # 4. Validation
        print("Validation:")
        try:
            settings.set_validation_mode("moodle", "strict")
            check("unknown system rejected", False, "no ValueError raised")
        except ValueError:
            check("unknown system rejected", True)
        try:
            settings.set_validation_mode("ldap", "nuclear")
            check("invalid mode rejected", False, "no ValueError raised")
        except ValueError:
            check("invalid mode rejected", True)

        # 5. Corrupt file degrades to defaults (file still readable? no — fall back)
        print("Degradation:")
        os.environ.pop("VALIDATION_MODE_LDAP", None)
        os.environ.pop("VALIDATION_MODE_CANVAS", None)
        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write("{ not valid json")
        check("corrupt file -> ldap default strict", settings.get_validation_mode("ldap") == "strict")
        check("corrupt file -> canvas default warn", settings.get_validation_mode("canvas") == "warn")
        os.remove(tmp_file)
        check("missing file -> ldap default strict", settings.get_validation_mode("ldap") == "strict")
        check("missing file -> canvas default warn", settings.get_validation_mode("canvas") == "warn")

    finally:
        if old_env_file is None:
            os.environ.pop("NCAD_SETTINGS_FILE", None)
        else:
            os.environ["NCAD_SETTINGS_FILE"] = old_env_file
        for system in settings.VALID_SYSTEMS:
            os.environ.pop(f"VALIDATION_MODE_{system.upper()}", None)

    print(f"\n{FAIL} failed, {PASS} passed")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
