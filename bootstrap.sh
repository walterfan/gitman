#!/usr/bin/env bash
# Remote installer for gitman.
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/walterfan/gitman/main/bootstrap.sh | bash
set -euo pipefail

readonly REPOSITORY_URL="https://github.com/walterfan/gitman"
readonly BRANCH="${GITMAN_BRANCH:-main}"
readonly ARCHIVE_URL="${REPOSITORY_URL}/archive/refs/heads/${BRANCH}.tar.gz"
readonly TEMP_DIR="$(mktemp -d)"

info() { printf '[INFO] %s\n' "$*"; }
err() { printf '[ERROR] %s\n' "$*" >&2; }

cleanup() {
  rm -rf -- "${TEMP_DIR}"
}
trap cleanup EXIT

if ! command -v curl >/dev/null 2>&1; then
  err "curl is required to download gitman."
  exit 1
fi

if ! command -v tar >/dev/null 2>&1; then
  err "tar is required to extract gitman."
  exit 1
fi

archive_path="${TEMP_DIR}/gitman.tar.gz"
source_root="${TEMP_DIR}/source"

info "Downloading gitman (${BRANCH}) from ${REPOSITORY_URL}"
curl --fail --silent --show-error --location \
  --proto '=https' --tlsv1.2 \
  "${ARCHIVE_URL}" --output "${archive_path}"

archive_listing="$(tar -tzf "${archive_path}")"
while IFS= read -r archive_member; do
  case "${archive_member}" in
    /*|..|../*|*/../*|*/..)
      err "Unsafe path in downloaded archive: ${archive_member}"
      exit 1
      ;;
  esac
done <<< "${archive_listing}"

mkdir -p -- "${source_root}"
tar --extract --gzip --file "${archive_path}" --directory "${source_root}" --strip-components=1

if [[ ! -f "${source_root}/install.sh" ]]; then
  err "Unable to locate install.sh in the downloaded source."
  exit 1
fi

info "Running install.sh"
bash "${source_root}/install.sh"
