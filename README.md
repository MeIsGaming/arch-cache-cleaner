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
  - `found_paths`
  - `found_bytes`
  - `groups_total`
  - `groups_selected`

## Output & UI

- Farbmodi: `--color auto|always|never`
- Schöne Section-Header mit klaren Gruppenblöcken
- Zusammenfassung mit:
  - gefundener Pfadanzahl
  - geschätzter Gesamtgröße der gefundenen Caches
  - gewählten Gruppen
  - Erfolgs-/Fehlerzähler
- Optional `--debug` für extra Diagnosen

## Qualitätssicherung

- GitHub Actions CI läuft für Python `3.10`, `3.11`, `3.12`
- Checks:
  - `ruff check .`
  - `python -m py_compile cache_cleaner.py`
  - Smoke-Test `--list-groups`
  - Smoke-Test `--dry-run --yes --only dev --no-temp`

## AUR Automation

Es gibt einen automatischen Sync-Flow für `arch-cache-cleaner-git`:

- Script: `scripts/sync_aur.sh`
- Workflow: `.github/workflows/aur-sync.yml`

### Lokal manuell syncen

```bash
./scripts/sync_aur.sh
```

Wichtig: Das Script darf **nicht als root** laufen (wegen `makepkg`).

Nützliche Variablen:

- `SOURCE_DIR` (Standard: aktuelles Verzeichnis)
- `AUR_REPO` (Standard: `ssh://aur@aur.archlinux.org/arch-cache-cleaner-git.git`)
- `AUR_BRANCH` (Standard: `master`)
- `AUR_DIR` (optional lokales Zielverzeichnis)
- `PUSH_CHANGES=0` (nur Commit lokal, kein Push)

Beispiel ohne Push:

```bash
PUSH_CHANGES=0 AUR_DIR=~/Aurstuff/arch-cache-cleaner-git ./scripts/sync_aur.sh
```

### GitHub Auto-Sync aktivieren

1. In GitHub Repo-Settings ein Secret anlegen: `AUR_SSH_PRIVATE_KEY`
2. Private Key des AUR-SSH-Keys hinterlegen
3. Workflow `AUR Sync` manuell starten oder durch Änderungen an `PKGBUILD` triggern

Der Workflow regeneriert `.SRCINFO`, synced `PKGBUILD/.SRCINFO/LICENSE` und pusht nur bei echten Änderungen.

### `pkgrel`-Regel

- Bei Packaging-Änderungen (z. B. `PKGBUILD`, Installpfade, Dependencies, Workflow-relevante Paketdaten) `pkgrel` erhöhen.
- Bei reinem Upstream-Code-Update im `-git` Paket bleibt `pkgver=r0.0` + `pkgver()` dynamisch, `pkgrel` nur bei Bedarf erhöhen.

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
