# CLI & Beispiele (Deutsch)

Zurück: [Wiki Start (DE)](Home.de.md)

## Wichtigste Optionen

| Option | Zweck |
|---|---|
| `--dry-run` | Zeigt nur an, was gelöscht würde |
| `--yes` | Führt Gruppen ohne Rückfrage aus |
| `--only install,aur_build` | Nur bestimmte Gruppen ausführen |
| `--list-groups` | Gruppen + gefundene Pfade auflisten |
| `--no-temp` | Temp-Cleanup komplett aus |
| `--temp-days N` | Temp-Dateien älter als `N` Tage bereinigen |
| `--config FILE` | Anderes JSON-Profil laden |
| `--export-report FILE` | JSON-Report schreiben |
| `--color auto|always|never` | Farbausgabe steuern |
| `--debug` | Zusätzliche Diagnoseausgabe |

## Beispiele

Nur Vorschau:

```bash
python3 ./cache_cleaner.py --dry-run
```

Nur AUR-Cache, ohne Interaktion:

```bash
python3 ./cache_cleaner.py --dry-run --yes --only aur_build --no-temp
```

Gruppen auflisten:

```bash
python3 ./cache_cleaner.py --list-groups --config ./cache_paths.json
```

Report erzeugen:

```bash
python3 ./cache_cleaner.py --dry-run --yes --export-report ./cache-report.json
```
