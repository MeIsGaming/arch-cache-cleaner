# arch-cache-cleaner Wiki (English)

Welcome to the English docs for `arch-cache-cleaner`.

## Quick Start

```bash
python3 ./cache_cleaner.py --dry-run
```

## Navigation

- [CLI & Examples](CLI.en.md)
- [Config & Profiles](Config.en.md)
- [AUR & Automation](AUR.en.md)
- [Deutsche Wiki-Startseite](Home.de.md)

## Highlights

- Interactive and automation-friendly (`--yes`, `--only`, `--export-report`)
- Colorized output (`--color auto|always|never`)
- JSON reports for logging/automation
- AUR sync via script and GitHub Action
- Single central config file (`cache_paths.json`) with extended platform/package-manager paths

## Typical Safe Run

```bash
python3 ./cache_cleaner.py --dry-run --yes --only dev --no-temp --color always
```
