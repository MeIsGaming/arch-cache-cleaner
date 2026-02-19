# arch-cache-cleaner Wiki (Deutsch)

Willkommen zur deutschen Doku für `arch-cache-cleaner`.

## Schnellstart

```bash
python3 ./cache_cleaner.py --dry-run
```

## Navigation

- [CLI & Beispiele](CLI.de.md)
- [Config & Profile](Config.de.md)
- [AUR & Automation](AUR.de.md)
- [English Wiki Home](Home.en.md)

## Highlights

- Interaktiv oder voll automatisierbar (`--yes`, `--only`, `--export-report`)
- Farbige Ausgabe (`--color auto|always|never`)
- JSON-Report für Logs/Automation
- AUR-Sync per Script und GitHub Action
- Eine zentrale Config-Datei (`cache_paths.json`) mit erweiterten Plattform-/Manager-Pfaden

## Typischer Safe-Run

```bash
python3 ./cache_cleaner.py --dry-run --yes --only dev --no-temp --color always
```
