# arch-cache-cleaner

Interaktives Python-Skript zum sinnvollen Leeren von Cache-Verzeichnissen auf Linux, macOS und Windows.

## Features

- Interaktive Ja/Nein-Abfragen pro Kategorie
- Erkennt nur vorhandene Pfade und arbeitet damit dynamisch
- Plattform-Logik über OS-spezifische Dictionaries (einfach erweiterbar)
- Profile liegen extern in `cache_paths.json` (ohne Codeänderung erweiterbar)
- Deckt u. a. ab:
  - Linux: Installations-Caches (`pacman`, `apt`, `dnf`, `yum`, `zypper`, `xbps`, `apk`, `portage`)
  - Linux: AUR/Build-Helper (`yay`, `paru`, `pamac`, `trizen`, `pikaur`)
  - macOS: Homebrew/MacPorts Caches
  - Windows: Winget/Chocolatey/Scoop Caches
  - Dev-Tool-Caches (`pip`, `npm`, `pnpm`, `yarn`, `cargo`, `go`, `gradle`, `maven`)
  - User-Caches (Thumbnails, Browser, Fontconfig)
  - Optionale Bereinigung alter Temp-Dateien (plattformabhängig)
- Nutzt `sudo` automatisch, wenn notwendig und verfügbar
- Optionaler `--dry-run` Modus

## Nutzung

```bash
python3 ./cache_cleaner.py
```

Optional:

```bash
python3 ./cache_cleaner.py --dry-run
python3 ./cache_cleaner.py --quiet
python3 ./cache_cleaner.py --config ./cache_paths.json
python3 ./cache_cleaner.py --config ./cache_paths.custom.json
python3 ./cache_cleaner.py --list-groups
python3 ./cache_cleaner.py --only install,aur_build --dry-run
python3 ./cache_cleaner.py --yes --only aur_build --dry-run
python3 ./cache_cleaner.py --yes --temp-days 7 --dry-run
python3 ./cache_cleaner.py --color always --dry-run
python3 ./cache_cleaner.py --export-report ./cache-report.json --dry-run
python3 ./cache_cleaner.py --debug --list-groups
```

## Wichtige CLI-Optionen

- `--yes`: Bereinigt Gruppen ohne Rückfrage
- `--only install,aur_build`: Führt nur diese Gruppen aus
- `--list-groups`: Zeigt Gruppen + vorhandene Pfade und beendet
- `--temp-days N`: Bereinigt Temp-Dateien älter als `N` Tage ohne Temp-Nachfrage
- `--no-temp`: Überspringt Temp-Bereinigung komplett
- `--config /pfad/datei.json`: Lädt ein eigenes Profil
- `--export-report /pfad/report.json`: Schreibt Laufdaten als JSON-Report
- `--color auto|always|never`: Steuert farbige Ausgabe
- `--debug`: Zusätzliche Diagnoseausgaben (z. B. aktive Gruppen, Config-Pfad)

Hinweis zu `--yes`: Temp-Bereinigung bleibt standardmäßig aus Sicherheitsgründen aus, solange `--temp-days` nicht gesetzt ist.

## Report-Format (kurz)

Der JSON-Report enthält u. a.:

- Zeitpunkt und Plattform
- verwendete Optionen
- pro Gruppe: gefundene Pfade, bereinigt, fehlgeschlagen
- Temp-Cleanup-Status
- Gesamtsummen

## Qualitätssicherung

- GitHub Actions CI läuft für Python `3.10`, `3.11`, `3.12`
- Checks:
  - `ruff check .`
  - `python -m py_compile cache_cleaner.py`
  - Smoke-Test `--list-groups`
  - Smoke-Test `--dry-run --yes --only dev --no-temp`

Legacy-Wrapper (weiterhin verfügbar):

```bash
./cache-cleaner.sh
```

## Config erweitern

Die Datei `cache_paths.json` enthält alle Plattform-Profile.

Schema pro Gruppe:

```json
{
  "linux": {
    "group_key": {
      "title": "Titel in der Ausgabe",
      "prompt": "Interaktive Frage",
      "paths": ["/path/one", "~/path/two", "/tmp/{user}-build"]
    }
  }
}
```

- Unterstützte Plattform-Keys: `linux`, `darwin`, `win32`
- `{user}` wird automatisch durch den aktuellen User ersetzt
- Existierende Pfade werden dynamisch erkannt

Zusätzlich liegt ein erweitertes Beispielprofil bereit: `cache_paths.custom.json`.

## Hinweis

Systemweite Caches benötigen je nach Plattform erhöhte Rechte. Unter Linux/macOS nutzt das Skript bei Bedarf `sudo`.
