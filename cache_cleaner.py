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
from typing import Any


@dataclass(frozen=True)
class CacheGroup:
    title: str
    prompt: str
    paths: list[str]


@dataclass(frozen=True)
class CliStyle:
    enabled: bool

    def color(self, text: str, code: str) -> str:
        if not self.enabled:
            return text
        return f"\033[{code}m{text}\033[0m"

    def info(self, text: str) -> str:
        return self.color(text, "36")

    def warn(self, text: str) -> str:
        return self.color(text, "33")

    def error(self, text: str) -> str:
        return self.color(text, "31")

    def success(self, text: str) -> str:
        return self.color(text, "32")

    def title(self, text: str) -> str:
        return self.color(text, "1;35")

    def subtitle(self, text: str) -> str:
        return self.color(text, "1;34")

    def dim(self, text: str) -> str:
        return self.color(text, "2")

    def accent(self, text: str) -> str:
        return self.color(text, "1;36")


def resolve_default_config_path() -> Path:
    env_path = os.environ.get("ARCH_CACHE_CLEANER_CONFIG")
    if env_path:
        return Path(os.path.expanduser(os.path.expandvars(env_path))).resolve(strict=False)

    candidates = [
        Path(__file__).with_name("cache_paths.json"),
        Path("/usr/share/arch-cache-cleaner/cache_paths.json"),
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve(strict=False)

    return candidates[0].resolve(strict=False)


def parse_cache_config(raw: dict[str, Any]) -> dict[str, dict[str, CacheGroup]]:
    parsed: dict[str, dict[str, CacheGroup]] = {}

    for platform_key, group_map in raw.items():
        if not isinstance(platform_key, str) or not isinstance(group_map, dict):
            continue

        groups: dict[str, CacheGroup] = {}
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

            groups[group_key] = CacheGroup(
                title=title, prompt=prompt, paths=paths)

        if groups:
            parsed[platform_key] = groups

    if not parsed:
        raise ValueError("Config enthält keine gültigen Gruppen")

    return parsed


def load_cache_paths(config_path: Path) -> dict[str, dict[str, CacheGroup]]:
    if not config_path.exists():
        raise FileNotFoundError(f"Config-Datei nicht gefunden: {config_path}")

    raw = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Config muss ein JSON-Objekt sein")
    return parse_cache_config(raw)


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


def dedupe_paths(paths: list[Path]) -> list[Path]:
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path).lower() if os.name == "nt" else str(path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def path_exists(path: Path) -> bool:
    try:
        return path.exists()
    except OSError:
        return False


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


def fast_dir_size(path: Path) -> int | None:
    if os.name != "posix":
        return None
    if shutil.which("du") is None:
        return None
    try:
        result = subprocess.run(
            ["du", "-sb", str(path)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return None
        value = result.stdout.strip().split("\t", 1)[0]
        return int(value)
    except (OSError, ValueError):
        return None


def size_of_path(path: Path) -> int:
    if not path_exists(path):
        return 0
    try:
        if path.is_file() or path.is_symlink():
            return path.stat().st_size
    except OSError:
        return 0

    fast_size = fast_dir_size(path)
    if fast_size is not None:
        return fast_size

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
    if not path_exists(path):
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

        result = subprocess.run(
            ["sudo", "rm", "-rf", "--", str(path)], check=False)
        if result.returncode == 0:
            return True
        print(f"[WARN] Löschen fehlgeschlagen: {path}")
        return False
    except OSError:
        print(f"[WARN] Löschen fehlgeschlagen: {path}")
        return False


def clear_path_contents(path: Path, dry_run: bool) -> bool:
    if not path_exists(path):
        return True

    if path.is_file() or path.is_symlink():
        return remove_entry(path, dry_run=dry_run)

    ok = True
    for entry in path.iterdir():
        if not remove_entry(entry, dry_run=dry_run):
            ok = False
    return ok


def print_group_preview(group: CacheGroup, resolved_paths: list[Path], quiet: bool, style: CliStyle) -> tuple[int, int]:
    if not resolved_paths:
        if not quiet:
            print(style.dim(f"[INFO] {group.title}: nichts gefunden"))
        return 0, 0

    print("\n" + style.subtitle(f"✨ {group.title}"))
    print(style.dim("-" * 40))
    total_bytes = 0
    for path in resolved_paths:
        path_size = size_of_path(path)
        size = format_bytes(path_size)
        total_bytes += path_size
        print(f"  {style.accent('•')} {path} ({size})")
    return len(resolved_paths), total_bytes


def temp_roots(platform_key: str) -> list[Path]:
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


def clean_temp_older_than(days: int, platform_key: str, dry_run: bool) -> tuple[list[str], list[str]]:
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
    parser = argparse.ArgumentParser(
        description="Interaktiver Multi-Platform Cache-Cleaner")
    parser.add_argument("--dry-run", action="store_true",
                        help="Nur anzeigen, nichts löschen")
    parser.add_argument("--quiet", action="store_true", help="Weniger Ausgabe")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Alle gefundenen Gruppen ohne Rückfrage bereinigen (außer Temp, wenn --temp-days nicht gesetzt)",
    )
    parser.add_argument(
        "--only",
        default=None,
        help="Nur bestimmte Gruppen-Keys ausführen (kommagetrennt, z. B. install,aur_build)",
    )
    parser.add_argument(
        "--list-groups",
        action="store_true",
        help="Nur verfügbare Gruppen und vorhandene Pfade anzeigen, dann beenden",
    )
    parser.add_argument(
        "--no-temp",
        action="store_true",
        help="Temporäre Bereinigung überspringen",
    )
    parser.add_argument(
        "--temp-days",
        type=int,
        default=None,
        help="Temp-Dateien älter als N Tage bereinigen (ohne Nachfrage für Temp)",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Pfad zu JSON-Datei mit Cache-Profilen",
    )
    parser.add_argument(
        "--export-report",
        default=None,
        help="JSON-Report in diese Datei schreiben",
    )
    parser.add_argument(
        "--color",
        choices=("auto", "always", "never"),
        default="auto",
        help="Farbige Ausgabe: auto, always oder never",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Zusätzliche Diagnoseausgaben aktivieren",
    )
    return parser.parse_args()


def parse_only_groups(raw_only: str | None) -> set[str] | None:
    if raw_only is None:
        return None

    keys = {chunk.strip() for chunk in raw_only.split(",") if chunk.strip()}
    if not keys:
        return None
    return keys


def filter_groups(groups: dict[str, CacheGroup], only_keys: set[str] | None) -> dict[str, CacheGroup]:
    if not only_keys:
        return groups
    return {key: value for key, value in groups.items() if key in only_keys}


def print_group_overview(groups: dict[str, CacheGroup]) -> None:
    print("\nVerfügbare Gruppen")
    print("------------------")
    for key, group in groups.items():
        resolved = [expand_path(path) for path in group.paths]
        existing = dedupe_paths([path for path in resolved if path_exists(path)])
        print(f"- {key}: {group.title}")
        if existing:
            for path in existing:
                print(f"    * {path}")
        else:
            print("    * keine vorhandenen Pfade")


def debug_log(enabled: bool, style: CliStyle, message: str) -> None:
    if enabled:
        print(style.dim(f"[DEBUG] {message}"))


def colors_enabled(mode: str) -> bool:
    if mode == "always":
        return True
    if mode == "never":
        return False
    return sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def write_report(path: Path, report: dict[str, Any], style: CliStyle) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(style.success(f"[OK] Report geschrieben: {path}"))
        return True
    except OSError as exc:
        print(style.error(f"[ERROR] Report konnte nicht geschrieben werden ({path}): {exc}"))
        return False


def main() -> int:
    args = parse_args()
    style = CliStyle(enabled=colors_enabled(args.color))
    platform_key = detect_platform()
    raw_config_path = args.config if args.config else str(
        resolve_default_config_path())
    config_path = Path(os.path.expanduser(
        os.path.expandvars(raw_config_path))).resolve(strict=False)
    debug_log(args.debug, style, f"Resolved config path: {config_path}")
    try:
        cache_paths = load_cache_paths(config_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(style.error(f"[ERROR] Konnte Config nicht laden: {exc}"))
        return 1

    groups = cache_paths.get(platform_key)
    if groups is None:
        groups = cache_paths.get("linux")
    if groups is None and cache_paths:
        groups = next(iter(cache_paths.values()))
    if groups is None:
        print(style.error("[ERROR] Keine gültigen Cache-Gruppen verfügbar."))
        return 1

    only_keys = parse_only_groups(args.only)
    unknown_only_keys: set[str] = set()
    if only_keys:
        unknown_only_keys = only_keys.difference(groups.keys())
        groups = filter_groups(groups, only_keys)

    if not groups:
        print(style.error("[ERROR] Keine passenden Gruppen ausgewählt."))
        return 1

    print("\n" + style.title("Cache Cleaner (Python, Cross-Platform)"))
    print(style.title("======================================"))
    print(f"Detected OS: {platform.system()} ({platform_key})")
    print(f"Config: {config_path}")
    if only_keys:
        print(f"Gruppenfilter: {', '.join(sorted(only_keys))}")
        if unknown_only_keys:
            print(style.warn(f"[WARN] Unbekannte Gruppen ignoriert: {', '.join(sorted(unknown_only_keys))}"))
    if args.dry_run:
        print(style.warn("Modus: DRY-RUN (es wird nichts gelöscht)"))
    debug_log(args.debug, style, f"Active group keys: {', '.join(groups.keys())}")

    report: dict[str, Any] = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "platform": {
            "detected": platform.system(),
            "key": platform_key,
        },
        "config": str(config_path),
        "dry_run": args.dry_run,
        "options": {
            "yes": args.yes,
            "only": sorted(only_keys) if only_keys else [],
            "no_temp": args.no_temp,
            "temp_days": args.temp_days,
            "list_groups": args.list_groups,
            "color": args.color,
            "debug": args.debug,
        },
        "groups": [],
        "temp_cleanup": {
            "executed": False,
            "days": None,
            "cleaned": [],
            "failed": [],
        },
        "totals": {
            "cleaned": 0,
            "failed": 0,
            "found_paths": 0,
            "found_bytes": 0,
            "groups_total": len(groups),
            "groups_selected": 0,
        },
    }

    if args.list_groups:
        print_group_overview(groups)
        if args.export_report:
            report["groups"] = [
                {
                    "key": key,
                    "title": group.title,
                    "paths_found": [
                        str(path)
                        for path in [expand_path(p) for p in group.paths]
                        if path_exists(path)
                    ],
                    "selected": False,
                    "action": "list_only",
                    "cleaned": [],
                    "failed": [],
                }
                for key, group in groups.items()
            ]
            report_path = Path(os.path.expanduser(os.path.expandvars(args.export_report))).resolve(strict=False)
            write_report(report_path, report, style)
        return 0

    cleaned: list[str] = []
    failed: list[str] = []
    found_paths_total = 0
    found_bytes_total = 0
    selected_groups = 0

    for group_key, group in groups.items():
        resolved = [expand_path(p) for p in group.paths]
        existing = dedupe_paths([p for p in resolved if path_exists(p)])
        found_count, found_bytes = print_group_preview(group, existing, quiet=args.quiet, style=style)
        found_paths_total += found_count
        found_bytes_total += found_bytes
        debug_log(args.debug, style, f"Group {group_key}: {len(existing)} existing paths")

        group_report = {
            "key": group_key,
            "title": group.title,
            "paths_found": [str(path) for path in existing],
            "paths_found_count": found_count,
            "paths_found_bytes": found_bytes,
            "selected": False,
            "action": "skipped_no_paths" if not existing else "pending",
            "cleaned": [],
            "failed": [],
        }

        if not existing:
            report["groups"].append(group_report)
            continue

        should_clean = args.yes or ask_yes_no(group.prompt)
        if not should_clean:
            if not args.quiet:
                print(style.info(f"[INFO] Übersprungen: {group.title}"))
            group_report["action"] = "skipped_by_user"
            report["groups"].append(group_report)
            continue

        group_report["selected"] = True
        group_report["action"] = "processed"
        selected_groups += 1

        for path in existing:
            if clear_path_contents(path, dry_run=args.dry_run):
                cleaned.append(str(path))
                group_report["cleaned"].append(str(path))
            else:
                failed.append(str(path))
                group_report["failed"].append(str(path))

        report["groups"].append(group_report)

    run_temp = False
    temp_days = args.temp_days

    if args.no_temp:
        run_temp = False
    elif temp_days is not None:
        if temp_days < 0:
            print(style.warn("[WARN] --temp-days muss >= 0 sein, Temp-Bereinigung übersprungen."))
        else:
            run_temp = True
    elif args.yes:
        if not args.quiet:
            print(style.info("[INFO] Temp-Bereinigung im --yes Modus übersprungen (setze --temp-days N zum Aktivieren)."))
    elif ask_yes_no("Do you want to clean temporary files older than N days?"):
        value = input(
            "Delete files older than how many days? [7]: ").strip() or "7"
        if value.isdigit():
            temp_days = int(value)
            run_temp = True
        else:
            print(style.warn("[WARN] Ungültige Zahl, temporäre Bereinigung übersprungen."))

    if run_temp and temp_days is not None:
        temp_cleaned, temp_failed = clean_temp_older_than(
            temp_days, platform_key, dry_run=args.dry_run)
        cleaned.extend(temp_cleaned)
        failed.extend(temp_failed)
        report["temp_cleanup"] = {
            "executed": True,
            "days": temp_days,
            "cleaned": temp_cleaned,
            "failed": temp_failed,
        }
    else:
        report["temp_cleanup"]["executed"] = False

    report["totals"]["cleaned"] = len(cleaned)
    report["totals"]["failed"] = len(failed)
    report["totals"]["found_paths"] = found_paths_total
    report["totals"]["found_bytes"] = found_bytes_total
    report["totals"]["groups_selected"] = selected_groups

    print("\n" + style.subtitle("📊 Zusammenfassung"))
    print(style.subtitle("-------------"))
    print(f"{style.accent('•')} Gefundene Pfade: {found_paths_total}")
    print(f"{style.accent('•')} Gefundene Größe: {format_bytes(found_bytes_total)}")
    print(f"{style.accent('•')} Gewählte Gruppen: {selected_groups}/{len(groups)}")
    print(f"{style.accent('•')} Erfolgreich bearbeitet: {len(cleaned)}")
    if failed:
        print(style.warn(f"{style.accent('•')} Fehlgeschlagen/übersprungen wegen Rechten: {len(failed)}"))
    else:
        print(style.success(f"{style.accent('•')} Fehlgeschlagen/übersprungen wegen Rechten: {len(failed)}"))

    if cleaned:
        print("\nBereinigt:")
        for item in cleaned:
            print(f"  {style.success('✓')} {item}")

    if failed:
        print("\nNicht bereinigt:")
        for item in failed:
            print(f"  {style.warn('⚠')} {item}")

    if args.export_report:
        report_path = Path(os.path.expanduser(os.path.expandvars(args.export_report))).resolve(strict=False)
        write_report(report_path, report, style)

    print("\n" + style.success("Fertig."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
