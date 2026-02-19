#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="${SOURCE_DIR:-$(pwd)}"
AUR_REPO="${AUR_REPO:-ssh://aur@aur.archlinux.org/arch-cache-cleaner-git.git}"
AUR_BRANCH="${AUR_BRANCH:-master}"
AUR_DIR="${AUR_DIR:-}"
PUSH_CHANGES="${PUSH_CHANGES:-1}"
COMMIT_MESSAGE="${COMMIT_MESSAGE:-chore(aur): sync PKGBUILD + .SRCINFO}"

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "[ERROR] Required command not found: $cmd" >&2
    exit 1
  fi
}

require_cmd git
require_cmd makepkg

if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
  echo "[ERROR] scripts/sync_aur.sh must not run as root (makepkg restriction)." >&2
  exit 1
fi

if [[ ! -f "$SOURCE_DIR/PKGBUILD" ]]; then
  echo "[ERROR] PKGBUILD not found in SOURCE_DIR=$SOURCE_DIR" >&2
  exit 1
fi

work_dir="$(mktemp -d /tmp/aur-sync.XXXXXX)"
trap 'rm -rf "$work_dir"' EXIT

cp "$SOURCE_DIR/PKGBUILD" "$work_dir/PKGBUILD"
(
  cd "$work_dir"
  makepkg --printsrcinfo > .SRCINFO
)

# Keep repo metadata up to date as well.
cp "$work_dir/.SRCINFO" "$SOURCE_DIR/.SRCINFO"

if [[ -z "$AUR_DIR" ]]; then
  AUR_DIR="$work_dir/aur-repo"
fi

if [[ -d "$AUR_DIR/.git" ]]; then
  git -C "$AUR_DIR" fetch origin "$AUR_BRANCH"
  git -C "$AUR_DIR" checkout "$AUR_BRANCH"
  git -C "$AUR_DIR" reset --hard "origin/$AUR_BRANCH"
else
  rm -rf "$AUR_DIR"
  git clone "$AUR_REPO" "$AUR_DIR"
  git -C "$AUR_DIR" checkout -B "$AUR_BRANCH"
fi

install -Dm644 "$SOURCE_DIR/PKGBUILD" "$AUR_DIR/PKGBUILD"
install -Dm644 "$work_dir/.SRCINFO" "$AUR_DIR/.SRCINFO"

if [[ -f "$SOURCE_DIR/LICENSE" ]]; then
  install -Dm644 "$SOURCE_DIR/LICENSE" "$AUR_DIR/LICENSE"
fi

if git -C "$AUR_DIR" diff --quiet -- PKGBUILD .SRCINFO LICENSE 2>/dev/null; then
  echo "[INFO] No AUR changes detected."
  exit 0
fi

git -C "$AUR_DIR" add PKGBUILD .SRCINFO
if [[ -f "$AUR_DIR/LICENSE" ]]; then
  git -C "$AUR_DIR" add LICENSE
fi
git -C "$AUR_DIR" commit -m "$COMMIT_MESSAGE"

if [[ "$PUSH_CHANGES" == "1" ]]; then
  git -C "$AUR_DIR" push origin "$AUR_BRANCH"
  echo "[OK] AUR sync pushed to $AUR_REPO ($AUR_BRANCH)"
else
  echo "[INFO] PUSH_CHANGES=0, commit created locally only."
fi
