# CLI & Examples (English)

Back: [Wiki Home (EN)](Home.en.md)

## Main Options

| Option | Purpose |
|---|---|
| `--dry-run` | Show actions without deleting anything |
| `--yes` | Run groups without prompts |
| `--only install,aur_build` | Run only selected groups |
| `--list-groups` | List groups + detected paths |
| `--no-temp` | Skip temp cleanup entirely |
| `--temp-days N` | Cleanup temp files older than `N` days |
| `--config FILE` | Load a custom JSON profile |
| `--export-report FILE` | Write JSON report |
| `--color auto|always|never` | Control color output |
| `--debug` | Enable extra diagnostics |

## Examples

Preview only:

```bash
python3 ./cache_cleaner.py --dry-run
```

AUR cache only, non-interactive:

```bash
python3 ./cache_cleaner.py --dry-run --yes --only aur_build --no-temp
```

List groups:

```bash
python3 ./cache_cleaner.py --list-groups --config ./cache_paths.json
```

Write report:

```bash
python3 ./cache_cleaner.py --dry-run --yes --export-report ./cache-report.json
```
