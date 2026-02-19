# Config & Profile (Deutsch)

Zurück: [Wiki Start (DE)](Home.de.md)

## Standardprofile

- `cache_paths.json`: zentrale, erweiterte Profile für `linux`, `darwin`, `win32`

## Schema

```json
{
  "linux": {
    "group_key": {
      "title": "Titel",
      "prompt": "Interaktive Frage",
      "paths": ["/path/one", "~/path/two", "/tmp/{user}-build"]
    }
  }
}
```

## Hinweise

- Unterstützte Plattform-Keys: `linux`, `darwin`, `win32`
- `{user}` wird automatisch ersetzt
- Nur vorhandene Pfade werden angezeigt/verarbeitet

## Linux Gruppen (aktuell)

- `install` (Paketmanager-/System-Caches)
- `aur_build` (AUR Helper / Build)
- `containers` (Docker/Podman/Buildah)
- `dev` (Tooling/Compiler/SDK Caches)
- `browsers` (native Browser-Caches)
- `flatpak_apps` (Flatpak App-Caches)
- `gaming` (Steam/Launcher-Caches)
- `user` (allgemeine User-Caches)

## macOS Gruppen (aktuell)

- `install`, `containers`, `dev`, `browsers`, `gaming`, `user`

## Windows Gruppen (aktuell)

- `install`, `containers`, `dev`, `browsers`, `gaming`, `user`

## Config nutzen

```bash
python3 ./cache_cleaner.py --config ./cache_paths.json --list-groups
```

Nur Browser + Flatpak Browser-Caches:

```bash
python3 ./cache_cleaner.py --dry-run --yes --only browsers,flatpak_apps --no-temp
```

## Env Override

Du kannst die Default-Config global setzen:

```bash
export ARCH_CACHE_CLEANER_CONFIG=/pfad/zu/cache_paths.json
```
