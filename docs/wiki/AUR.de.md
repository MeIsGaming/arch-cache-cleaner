# AUR & Automation (Deutsch)

Zurück: [Wiki Start (DE)](Home.de.md)

## Paket

- Paketname: `arch-cache-cleaner-git`
- Packaging-Dateien: `PKGBUILD`, `.SRCINFO`, `LICENSE`

## `pkgrel`-Regel

- `pkgrel` erhöhen bei Packaging-Änderungen
- `pkgver=r0.0` bleibt bei `-git` Paket, die echte Version kommt aus `pkgver()`

## Lokaler Sync

```bash
./scripts/sync_aur.sh
```

Wichtig: nicht als root ausführen.

## Dry-Sync ohne Push

```bash
PUSH_CHANGES=0 AUR_DIR=~/Aurstuff/arch-cache-cleaner-git ./scripts/sync_aur.sh
```

## GitHub Automation

Workflow: `.github/workflows/aur-sync.yml`

Benötigtes Secret:

- `AUR_SSH_PRIVATE_KEY`

Der Workflow:

1. erstellt Non-Root Build-User
2. regeneriert `.SRCINFO`
3. synced `PKGBUILD/.SRCINFO/LICENSE`
4. pusht nur bei Änderungen
