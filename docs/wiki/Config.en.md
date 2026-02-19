# Config & Profiles (English)

Back: [Wiki Home (EN)](Home.en.md)

## Default Profiles

- `cache_paths.json`: central extended profiles for `linux`, `darwin`, `win32`

## Schema

```json
{
  "linux": {
    "group_key": {
      "title": "Title",
      "prompt": "Interactive prompt",
      "paths": ["/path/one", "~/path/two", "/tmp/{user}-build"]
    }
  }
}
```

## Notes

- Supported platform keys: `linux`, `darwin`, `win32`
- `{user}` is replaced automatically
- Only existing paths are listed/processed

## Linux groups (current)

- `install` (package manager/system caches)
- `aur_build` (AUR helper/build caches)
- `containers` (Docker/Podman/Buildah)
- `dev` (toolchain/compiler/SDK caches)
- `browsers` (native browser caches)
- `flatpak_apps` (Flatpak app caches)
- `gaming` (Steam/launcher caches)
- `user` (general user caches)

## macOS groups (current)

- `install`, `containers`, `dev`, `browsers`, `gaming`, `user`

## Windows groups (current)

- `install`, `containers`, `dev`, `browsers`, `gaming`, `user`

## Use Config

```bash
python3 ./cache_cleaner.py --config ./cache_paths.json --list-groups
```

Browser + Flatpak browser caches only:

```bash
python3 ./cache_cleaner.py --dry-run --yes --only browsers,flatpak_apps --no-temp
```

## Env Override

You can set a global default config:

```bash
export ARCH_CACHE_CLEANER_CONFIG=/path/to/cache_paths.json
```
