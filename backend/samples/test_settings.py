"""
Unit tests for the validation-mode settings registry (app/core/settings.py).

Run from the backend/ directory:
    .venv\\Scripts\\python.exe samples\\test_settings.py

Covers:
  - Every system defaults to warn.
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
        check("ldap defaults to warn", settings.get_validation_mode("ldap") == "warn")
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
        check("corrupt file -> ldap default warn", settings.get_validation_mode("ldap") == "warn")
        check("corrupt file -> canvas default warn", settings.get_validation_mode("canvas") == "warn")
        os.remove(tmp_file)
        check("missing file -> ldap default warn", settings.get_validation_mode("ldap") == "warn")
        check("missing file -> canvas default warn", settings.get_validation_mode("canvas") == "warn")

        # 6. Non-blocking required columns (Date of Birth for LDAP)
        print("Non-blocking columns:")
        from app.core.quercus_schema import (
            check_columns,
            blocking_missing_required,
            NON_BLOCKING_REQUIRED_COLUMNS,
            check_source_columns,
        )
        check(
            "ldap DOB is registered as non-blocking",
            NON_BLOCKING_REQUIRED_COLUMNS["ldap"] == ("Date of Birth",),
        )
        ldap_missing_dob = check_columns(
            "ldap",
            [
                "ID Number", "Course Code", "Course Description",
                "Course Instance Course Year", "Type", "First Name",
                "Last Name", "Term Email", "LDAP ID",
            ],
        )
        check("DOB missing is still reported as missing", "Date of Birth" in ldap_missing_dob["missing_required"])
        check(
            "ldap DOB-only missing -> nothing blocks",
            blocking_missing_required("ldap", ldap_missing_dob) == [],
        )
        ldap_missing_dob_and_id = check_columns(
            "ldap",
            [
                "Course Code", "Course Description",
                "Course Instance Course Year", "Type", "First Name",
                "Last Name", "Term Email", "LDAP ID",
            ],
        )
        check(
            "ldap DOB + ID Number missing -> only ID Number blocks",
            blocking_missing_required("ldap", ldap_missing_dob_and_id) == ["ID Number"],
        )
        canvas_missing_first = check_columns("canvas", ["ID Number", "Last Name", "Term Email"])
        check(
            "canvas missing column always blocks",
            blocking_missing_required("canvas", canvas_missing_first) == ["First Name"],
        )

        # 7. Quercus upload warning excludes non-blocking columns (DOB)
        print("Upload source warning columns:")
        source_without_dob = check_source_columns(
            [
                "ID Number", "Course Code", "Course Description",
                "Course Instance Course Year", "Type", "First Name",
                "Last Name", "Term Email", "LDAP ID",
            ],
        )
        check("DOB excluded from upload warning", "Date of Birth" not in source_without_dob)
        source_missing_first = check_source_columns(["ID Number", "Last Name", "Term Email"])
        check("genuine missing column still warned", "First Name" in source_missing_first)

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
