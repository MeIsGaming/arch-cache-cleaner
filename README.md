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
```

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
