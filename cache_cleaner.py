#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


@dataclass(frozen=True)
class CacheGroup:
    title: str
    prompt: str
    paths: List[str]


DEFAULT_CACHE_CONFIG: Dict[str, Dict[str, Dict[str, Any]]] = {
    "linux": {
        "install": {
            "title": "Installations-Cache (pacman/apt/dnf/zypp/...)",
            "prompt": "Do you want to remove installation cache (yay, pacman, apt, dnf, ...)?",
            "paths": [
                "/var/cache/pacman/pkg",
                "/var/cache/apt/archives",
                "/var/cache/apt/archives/partial",
                "/var/cache/dnf",
                "/var/cache/yum",
                "/var/cache/zypp",
                "/var/cache/xbps",
                "/var/cache/apk",
                "/var/cache/eopkg/packages",
                "/var/cache/portage/distfiles",
                "/var/cache/edb/dep",
                "/var/lib/snapd/cache",
                "/var/cache/pacstall",
            ],
        },
        "aur_build": {
            "title": "AUR/Build-Cache (yay/paru/pamac/...)",
            "prompt": "Do you want to remove AUR/build helper cache (yay, paru, pamac, ...)?",
            "paths": [
                "~/.cache/yay",
                "~/.cache/paru",
                "~/.cache/trizen",
                "~/.cache/pikaur",
                "~/.cache/pamac",
                "/var/tmp/pamac-build-{user}",
                "/tmp/pamac-build-{user}",
            ],
        },
        "dev": {
            "title": "Dev-Tool-Caches (pip/npm/cargo/...)",
            "prompt": "Do you want to remove developer tool caches (pip, npm, cargo, ...)?",
            "paths": [
                "~/.cache/pip",
                "~/.npm/_cacache",
                "~/.cache/pnpm",
                "~/.cache/yarn",
                "~/.cache/go-build",
                "~/.cargo/registry/cache",
                "~/.cargo/git/db",
                "~/.gradle/caches",
                "~/.m2/repository",
            ],
        },
        "user": {
            "title": "User-Cache (thumbnails/browser/fontconfig)",
            "prompt": "Do you want to remove user cache (thumbnails/browser/fontconfig)?",
            "paths": [
                "~/.cache/thumbnails",
                "~/.cache/fontconfig",
                "~/.cache/mozilla",
                "~/.cache/google-chrome",
                "~/.cache/chromium",
                "~/.cache/BraveSoftware",
            ],
        },
    },
    "darwin": {
        "install": {
            "title": "Installations-Cache (homebrew/macports)",
            "prompt": "Do you want to remove installation cache (Homebrew, MacPorts)?",
            "paths": [
                "~/Library/Caches/Homebrew",
                "/Library/Caches/Homebrew",
                "/opt/local/var/macports/distfiles",
            ],
        },
        "dev": {
            "title": "Dev-Tool-Caches (pip/npm/cargo/...)",
            "prompt": "Do you want to remove developer tool caches (pip, npm, cargo, ...)?",
            "paths": [
                "~/Library/Caches/pip",
                "~/.cache/pip",
                "~/.npm/_cacache",
                "~/Library/Caches/Yarn",
                "~/.cache/pnpm",
                "~/Library/Caches/go-build",
                "~/.cargo/registry/cache",
                "~/.cargo/git/db",
                "~/.gradle/caches",
                "~/.m2/repository",
            ],
        },
        "user": {
            "title": "User-Cache (browser/font)",
            "prompt": "Do you want to remove user cache (browser/font/thumbnail)?",
            "paths": [
                "~/Library/Caches/Google/Chrome",
                "~/Library/Caches/Chromium",
                "~/Library/Caches/BraveSoftware",
                "~/Library/Caches/Firefox",
                "~/Library/Caches/com.apple.iconservices.store",
            ],
        },
    },
    "win32": {
        "install": {
            "title": "Installations-Cache (winget/choco/scoop)",
            "prompt": "Do you want to remove installation cache (winget/choco/scoop)?",
            "paths": [
                "~\\AppData\\Local\\Packages\\Microsoft.DesktopAppInstaller_8wekyb3d8bbwe\\LocalState\\DiagOutputDir",
                "~\\AppData\\Local\\Packages\\Microsoft.DesktopAppInstaller_8wekyb3d8bbwe\\LocalState\\TempState",
                "~\\AppData\\Local\\NuGet\\v3-cache",
                "C:\\ProgramData\\chocolatey\\lib-bkp",
                "~\\scoop\\cache",
            ],
        },
        "dev": {
            "title": "Dev-Tool-Caches (pip/npm/cargo/...)",
            "prompt": "Do you want to remove developer tool caches (pip, npm, cargo, ...)?",
            "paths": [
                "~\\AppData\\Local\\pip\\Cache",
                "~\\AppData\\Roaming\\npm-cache",
                "~\\AppData\\Local\\pnpm\\cache",
                "~\\AppData\\Local\\Yarn\\Cache",
                "~\\.cargo\\registry\\cache",
                "~\\.cargo\\git\\db",
                "~\\.gradle\\caches",
                "~\\.m2\\repository",
            ],
        },
        "user": {
            "title": "User-Cache (browser/thumbnail)",
            "prompt": "Do you want to remove user cache (browser/thumbnail)?",
            "paths": [
                "~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Cache",
                "~\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Cache",
                "~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Cache",
                "~\\AppData\\Local\\Microsoft\\Windows\\Explorer",
            ],
        },
    },
}

DEFAULT_CONFIG_PATH = Path(__file__).with_name("cache_paths.json")


def parse_cache_config(raw: Dict[str, Any]) -> Dict[str, Dict[str, CacheGroup]]:
    parsed: Dict[str, Dict[str, CacheGroup]] = {}

    for platform_key, group_map in raw.items():
        if not isinstance(platform_key, str) or not isinstance(group_map, dict):
            continue

        groups: Dict[str, CacheGroup] = {}
        for group_key, group_data in group_map.items():
            if not isinstance(group_key, str) or not isinstance(group_data, dict):
                continue

            title = group_data.get("title")
            prompt = group_data.get("prompt")
            paths = group_data.get("paths")

            if not isinstance(title, str) or not isinstance(prompt, str) or not isinstance(paths, list):
                continue
            if not all(isinstance(path, str) for path in paths):
                continue

            groups[group_key] = CacheGroup(title=title, prompt=prompt, paths=paths)

        if groups:
            parsed[platform_key] = groups

    if not parsed:
        raise ValueError("Config enthält keine gültigen Gruppen")

    return parsed


def load_cache_paths(config_path: Path) -> Tuple[Dict[str, Dict[str, CacheGroup]], bool]:
    if config_path.exists():
        try:
            raw = json.loads(config_path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("Config muss ein JSON-Objekt sein")
            return parse_cache_config(raw), True
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"[WARN] Konnte Config nicht laden ({config_path}): {exc}")
            print("[WARN] Fallback auf eingebettete Defaults.")
    else:
        print(f"[WARN] Config-Datei nicht gefunden: {config_path}")
        print("[WARN] Fallback auf eingebettete Defaults.")

    return parse_cache_config(DEFAULT_CACHE_CONFIG), False


def detect_platform() -> str:
    value = sys.platform
    if value.startswith("linux"):
        return "linux"
    if value == "darwin":
        return "darwin"
    if value in {"win32", "cygwin", "msys"}:
        return "win32"
    return "linux"


def expand_path(raw: str) -> Path:
    user = os.environ.get("USER") or os.environ.get("USERNAME") or "user"
    formatted = raw.format(user=user)
    return Path(os.path.expanduser(os.path.expandvars(formatted))).resolve(strict=False)


def ask_yes_no(prompt: str) -> bool:
    while True:
        answer = input(f"{prompt} [y/N]: ").strip().lower()
        if answer in {"", "n", "no"}:
            return False
        if answer in {"y", "yes"}:
            return True
        print("Bitte y oder n eingeben.")


def format_bytes(size: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size} B"


def size_of_path(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        if path.is_file() or path.is_symlink():
            return path.stat().st_size
    except OSError:
        return 0

    total = 0
    for root, dirs, files in os.walk(path, onerror=lambda _e: None):
        for name in files:
            file_path = Path(root) / name
            try:
                if not file_path.is_symlink():
                    total += file_path.stat().st_size
            except OSError:
                pass
        for name in dirs:
            dir_path = Path(root) / name
            try:
                if dir_path.is_symlink():
                    total += dir_path.stat().st_size
            except OSError:
                pass
    return total


def dangerous_path(path: Path) -> bool:
    raw = str(path)
    blocked = {
        "/",
        str(Path.home().anchor),
        "C:\\",
        "D:\\",
        "E:\\",
    }
    return raw in blocked


def remove_entry(path: Path, dry_run: bool) -> bool:
    if not path.exists():
        return True

    if dangerous_path(path):
        print(f"[WARN] Übersprungen (unsicherer Pfad): {path}")
        return False

    if dry_run:
        print(f"[DRY-RUN] remove: {path}")
        return True

    try:
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink()
        return True
    except PermissionError:
        if os.name != "posix" or shutil.which("sudo") is None:
            print(f"[WARN] Keine Rechte für: {path}")
            return False

        result = subprocess.run(["sudo", "rm", "-rf", "--", str(path)], check=False)
        if result.returncode == 0:
            return True
        print(f"[WARN] Löschen fehlgeschlagen: {path}")
        return False
    except OSError:
        print(f"[WARN] Löschen fehlgeschlagen: {path}")
        return False


def clear_path_contents(path: Path, dry_run: bool) -> bool:
    if not path.exists():
        return True

    if path.is_file() or path.is_symlink():
        return remove_entry(path, dry_run=dry_run)

    ok = True
    for entry in path.iterdir():
        if not remove_entry(entry, dry_run=dry_run):
            ok = False
    return ok


def print_group_preview(group: CacheGroup, resolved_paths: List[Path], quiet: bool) -> None:
    if not resolved_paths:
        if not quiet:
            print(f"[INFO] {group.title}: nichts gefunden")
        return

    print(f"\n{group.title}")
    print("-" * 40)
    for path in resolved_paths:
        size = format_bytes(size_of_path(path))
        print(f"  - {path} ({size})")


def temp_roots(platform_key: str) -> List[Path]:
    if platform_key == "win32":
        roots = [tempfile.gettempdir()]
        for key in ("TMP", "TEMP"):
            value = os.environ.get(key)
            if value:
                roots.append(value)
        roots.append(r"C:\\Windows\\Temp")
        unique = []
        seen = set()
        for root in roots:
            path = Path(root).resolve(strict=False)
            if str(path).lower() not in seen:
                seen.add(str(path).lower())
                unique.append(path)
        return unique

    return [Path("/tmp"), Path("/var/tmp")]


def clean_temp_older_than(days: int, platform_key: str, dry_run: bool) -> tuple[List[str], List[str]]:
    cleaned, failed = [], []
    now = datetime.now().timestamp()
    threshold_seconds = days * 86400

    for root in temp_roots(platform_key):
        if not root.exists() or not root.is_dir():
            continue

        root_cleaned = False
        for entry in root.iterdir():
            try:
                age_seconds = now - entry.stat().st_mtime
            except OSError:
                continue

            if age_seconds < threshold_seconds:
                continue

            if remove_entry(entry, dry_run=dry_run):
                root_cleaned = True
            else:
                failed.append(f"{entry}")

        if root_cleaned:
            cleaned.append(f"{root} (älter als {days} Tage)")

    return cleaned, failed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interaktiver Multi-Platform Cache-Cleaner")
    parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, nichts löschen")
    parser.add_argument("--quiet", action="store_true", help="Weniger Ausgabe")
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Pfad zu JSON-Datei mit Cache-Profilen",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    platform_key = detect_platform()
    config_path = Path(os.path.expanduser(os.path.expandvars(args.config))).resolve(strict=False)
    cache_paths, config_loaded = load_cache_paths(config_path)

    groups = cache_paths.get(platform_key)
    if groups is None:
        groups = cache_paths.get("linux")
    if groups is None and cache_paths:
        groups = next(iter(cache_paths.values()))
    if groups is None:
        print("[ERROR] Keine gültigen Cache-Gruppen verfügbar.")
        return 1

    print("\nCache Cleaner (Python, Cross-Platform)")
    print("======================================")
    print(f"Detected OS: {platform.system()} ({platform_key})")
    if config_loaded:
        print(f"Config: {config_path}")
    if args.dry_run:
        print("Modus: DRY-RUN (es wird nichts gelöscht)")

    cleaned: List[str] = []
    failed: List[str] = []

    for group in groups.values():
        resolved = [expand_path(p) for p in group.paths]
        existing = [p for p in resolved if p.exists()]
        print_group_preview(group, existing, quiet=args.quiet)

        if not existing:
            continue

        if not ask_yes_no(group.prompt):
            if not args.quiet:
                print(f"[INFO] Übersprungen: {group.title}")
            continue

        for path in existing:
            if clear_path_contents(path, dry_run=args.dry_run):
                cleaned.append(str(path))
            else:
                failed.append(str(path))

    if ask_yes_no("Do you want to clean temporary files older than N days?"):
        value = input("Delete files older than how many days? [7]: ").strip() or "7"
        if value.isdigit():
            temp_cleaned, temp_failed = clean_temp_older_than(int(value), platform_key, dry_run=args.dry_run)
            cleaned.extend(temp_cleaned)
            failed.extend(temp_failed)
        else:
            print("[WARN] Ungültige Zahl, temporäre Bereinigung übersprungen.")

    print("\nZusammenfassung")
    print("-------------")
    print(f"Erfolgreich bearbeitet: {len(cleaned)}")
    print(f"Fehlgeschlagen/übersprungen wegen Rechten: {len(failed)}")

    if cleaned:
        print("\nBereinigt:")
        for item in cleaned:
            print(f"  - {item}")

    if failed:
        print("\nNicht bereinigt:")
        for item in failed:
            print(f"  - {item}")

    print("\nFertig.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
