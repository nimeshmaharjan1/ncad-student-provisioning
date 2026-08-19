#!/usr/bin/env python3
"""Self-healing setup step for the NCAD provisioning launchers.

Runs under the SYSTEM Python (3.10+). Creates or repairs everything the
launchers need and skips whatever is already healthy:

  1. backend/.venv              create / recreate if broken
  2. Python deps                (re)install when requirements.txt changes
  3. words.txt                  validate the passcode word list (never auto-created)
  4. frontend/node_modules      (re)install when package files change
  5. frontend/.env              create from the local default if missing
  6. frontend/.next             rebuild when the source changes

`words.txt` is the one asset this script will not fabricate: it is a secret
that travels out-of-band (like the baselines). If it is missing the launcher
hard-stops with instructions, unless PROVISION_REQUIRE_WORDS=0 opts into the
weak fallback (demo machines only).

Exits non-zero if any step cannot be repaired.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIN_WORDS = 100
DEFAULT_ENV = "NEXT_PUBLIC_API_URL=http://127.0.0.1:8000\n"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str | None:
    try:
        return _sha(path.read_bytes())
    except OSError:
        return None


def sha256_tree(dir: Path, exclude: tuple[str, ...] = ()) -> str:
    h = hashlib.sha256()
    if not dir.exists():
        return h.hexdigest()
    for f in sorted(dir.rglob("*")):
        if not f.is_file():
            continue
        parts = f.relative_to(dir).parts
        if any(part in exclude for part in parts):
            continue
        h.update("/".join(parts).encode("utf-8"))
        try:
            h.update(f.read_bytes())
        except OSError:
            pass
    return h.hexdigest()


def run(args: list[str], cwd: Path = ROOT, quiet: bool = False) -> int:
    kwargs: dict = {"cwd": str(cwd), "text": True}
    if quiet:
        kwargs.update(stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        return subprocess.run(args, **kwargs).returncode
    except FileNotFoundError:
        print(f"[ERROR] Could not run: {args[0]}")
        return -1


def npm_cmd() -> list[str]:
    return ["npm.cmd"] if os.name == "nt" else ["npm"]


def venv_python() -> Path:
    if os.name == "nt":
        return ROOT / "backend" / ".venv" / "Scripts" / "python.exe"
    return ROOT / "backend" / ".venv" / "bin" / "python"


def step(n: int, total: int, name: str) -> None:
    print(f"\n[{n}/{total}] {name}")


# ---------------------------------------------------------------------------
# Step 1 + 2 helpers (venv is shared between steps 1 and 2)
# ---------------------------------------------------------------------------
def _create_venv() -> bool:
    venv_dir = ROOT / "backend" / ".venv"
    shutil.rmtree(venv_dir, ignore_errors=True)
    print("[INFO] Creating virtual environment...")
    if run([sys.executable, "-m", "venv", str(venv_dir)]) != 0:
        print("[ERROR] Failed to create the virtual environment.")
        return False
    return True


def ensure_venv() -> bool:
    vp = venv_python()
    if not vp.exists():
        if not _create_venv():
            return False
        print("[INFO] Virtual environment created.")
        return True
    if run([str(vp), "-m", "pip", "--version"], quiet=True) != 0:
        print("[WARN] Virtual environment is broken - recreating...")
        if not _create_venv():
            return False
        print("[INFO] Virtual environment recreated.")
        return True
    print("[SKIP] already healthy.")
    return True


def ensure_python_deps() -> bool:
    req = ROOT / "backend" / "requirements.txt"
    marker = ROOT / "backend" / ".venv" / ".requirements.sha256"
    vp = venv_python()
    current = sha256_file(req)
    stored = marker.read_text().strip() if marker.exists() else None
    if stored == current:
        print("[SKIP] requirements.txt unchanged.")
        return True
    print("[INFO] Installing Python dependencies...")
    if run([str(vp), "-m", "pip", "install", "-r", str(req)]) != 0:
        print("[WARN] Install failed - recreating venv and retrying...")
        if not _create_venv():
            return False
        if run([str(venv_python()), "-m", "pip", "install", "-r", str(req)]) != 0:
            print("[ERROR] Failed to install Python dependencies.")
            return False
    if current:
        marker.write_text(current, encoding="utf-8")
    print("[INFO] Dependencies up to date.")
    return True


# ---------------------------------------------------------------------------
# Step 3: words.txt
# ---------------------------------------------------------------------------
_WORDS_INSTRUCTIONS = """\
The passcode word list is missing. Without it, passcodes would fall back to
a weak built-in 15-word list - not acceptable.

Fix it either way:

  Option 1 - copy the file into the project (recommended):
    Copy the word list to:  backend\\app\\utils\\words.txt
    (full path: %s\\backend\\app\\utils\\words.txt)

  Option 2 - keep it elsewhere and point to it via PASSCODE_WORD_FILE:
    That variable tells the system where the list lives instead of the
    default location. Set it to the file's ABSOLUTE path:
      Windows cmd (this session):   set PASSCODE_WORD_FILE=C:\\path\\to\\words.txt
      Windows cmd (permanent):      setx PASSCODE_WORD_FILE "C:\\path\\to\\words.txt"
      PowerShell:                   $env:PASSCODE_WORD_FILE = "C:\\path\\to\\words.txt"
      Linux/macOS:                  export PASSCODE_WORD_FILE=/path/to/words.txt

Where to get the file:
  It is deliberately NOT in the repo - it travels separately, like the
  baselines. Get it from the system owner (NCAD IT Support). Any NCAD
  channel that delivers the intact file works (shared drive, USB, Teams,
  SFTP): secrecy is not the concern, integrity is. It should contain
  1,668 words, one per line; the launcher validates it.

Then run the launcher again. For demo machines that may run without it,
set PROVISION_REQUIRE_WORDS=0 to proceed with the fallback.
""" % str(ROOT)


def _words_count(p: Path) -> int | None:
    try:
        return sum(1 for line in p.open(encoding="utf-8") if line.strip())
    except OSError as e:
        print(f"[ERROR] Cannot read words.txt: {e}")
        return None


def check_words() -> bool:
    env_path = os.environ.get("PASSCODE_WORD_FILE")
    if env_path:
        p = Path(env_path)
        if not p.exists():
            print("[ERROR] PASSCODE_WORD_FILE is set but the file is missing: " + env_path)
            print("        Fix the path or unset the variable (see ONBOARDING.md).")
            return False
    else:
        p = ROOT / "backend" / "app" / "utils" / "words.txt"

    if p.exists():
        count = _words_count(p)
        if count is None:
            return False
        if count < MIN_WORDS:
            print(f"[WARN] words.txt has only {count} words (expected {MIN_WORDS}+). This looks like")
            print("       the built-in fallback, not the real list - replace it before generating")
            print("       passcodes. The launcher never deletes this file.")
        else:
            print(f"[SKIP] {count} words present.")
        return True

    if os.environ.get("PROVISION_REQUIRE_WORDS") == "0":
        print("[WARN] words.txt not found but PROVISION_REQUIRE_WORDS=0 - proceeding with the")
        print("       weak 15-word fallback. Only for demo machines.")
        return True

    if not sys.stdin.isatty():
        print("[ERROR] " + _WORDS_INSTRUCTIONS)
        return False

    print("[WARN] words.txt not found - the launcher will not run without it.")
    for _ in range(3):
        answer = input("words.txt not found. Do you have it? (y/N): ").strip().lower()
        if answer in ("y", "yes"):
            print("Place it at backend\\app\\utils\\words.txt (or set PASSCODE_WORD_FILE),")
            input("then press Enter to re-check...")
            if p.exists():
                count = _words_count(p)
                if count is None:
                    return False
                print(f"[INFO] words.txt found - {count} words present.")
                return True
            print("[WARN] Still not found.")
            continue
        print("[ERROR] " + _WORDS_INSTRUCTIONS)
        return False
    print("[ERROR] " + _WORDS_INSTRUCTIONS)
    return False


# ---------------------------------------------------------------------------
# Steps 4-6: frontend
# ---------------------------------------------------------------------------
def ensure_node_deps() -> bool:
    fe = ROOT / "frontend"
    pkg = fe / "package.json"
    lock = fe / "package-lock.json"
    nm = fe / "node_modules"
    marker = nm / ".deps.sha256"

    pkg_hash = sha256_file(pkg) or ""
    lock_hash = sha256_file(lock) or ""
    current = _sha((pkg_hash + lock_hash).encode("utf-8"))
    stored = marker.read_text().strip() if marker.exists() else None

    if nm.exists() and stored == current:
        print("[SKIP] package files unchanged.")
        return True
    print("[INFO] Installing frontend dependencies...")
    cmd = npm_cmd() + ["install", "--no-audit", "--no-fund"]
    if run(cmd, cwd=fe) != 0:
        print("[WARN] npm install failed - removing node_modules and retrying...")
        shutil.rmtree(nm, ignore_errors=True)
        if run(cmd, cwd=fe) != 0:
            print("[ERROR] Failed to install frontend dependencies.")
            return False
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(current, encoding="utf-8")
    print("[INFO] Frontend dependencies up to date.")
    return True


def ensure_env() -> bool:
    env = ROOT / "frontend" / ".env"
    if env.exists():
        content = env.read_text(encoding="utf-8")
        if "NEXT_PUBLIC_API_URL" not in content:
            print("[WARN] frontend/.env exists but has no NEXT_PUBLIC_API_URL - appending default.")
            with env.open("a", encoding="utf-8") as f:
                f.write(DEFAULT_ENV)
        else:
            print("[SKIP] already present.")
        return True
    env.write_text(DEFAULT_ENV, encoding="utf-8")
    print("[INFO] Created frontend/.env with the local backend URL.")
    return True


def ensure_build() -> bool:
    fe = ROOT / "frontend"
    next_dir = fe / ".next"
    marker = next_dir / ".build.sha256"
    # Inputs to the build: frontend source (minus generated node_modules/.next/docs)
    # plus the repo docs/ that sync-docs.mjs copies into frontend/docs/ during prebuild.
    current = (
        sha256_tree(fe, exclude=("node_modules", ".next", "docs"))
        + sha256_tree(ROOT / "docs")
    )
    stored = marker.read_text().strip() if marker.exists() else None

    if next_dir.exists() and stored == current:
        print("[SKIP] source unchanged.")
        return True
    print("[INFO] Building frontend (this may take a minute)...")
    cmd = npm_cmd() + ["run", "build"]
    if run(cmd, cwd=fe) != 0:
        print("[WARN] Build failed - removing .next and retrying...")
        shutil.rmtree(next_dir, ignore_errors=True)
        if run(cmd, cwd=fe) != 0:
            print("[ERROR] Frontend build failed.")
            return False
    next_dir.mkdir(parents=True, exist_ok=True)
    marker.write_text(current, encoding="utf-8")
    print("[INFO] Build complete.")
    return True


# ---------------------------------------------------------------------------
def main() -> int:
    total = 6
    ok = True

    step(1, total, "Python virtual environment")
    ok = ensure_venv() and ok

    step(2, total, "Python dependencies")
    ok = ensure_python_deps() and ok

    step(3, total, "Passcode word list (words.txt)")
    ok = check_words() and ok

    step(4, total, "Frontend dependencies (node_modules)")
    ok = ensure_node_deps() and ok

    step(5, total, "Frontend environment (.env)")
    ok = ensure_env() and ok

    step(6, total, "Frontend build (.next)")
    ok = ensure_build() and ok

    print("\n" + ("Setup complete - all systems go." if ok else "Setup finished with warnings/errors above."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())