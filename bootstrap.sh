#!/usr/bin/env bash
set -euo pipefail

readonly REPOSITORY_URL="https://github.com/walterfan/gitman"
readonly ARCHIVE_URL="${REPOSITORY_URL}/archive/refs/heads/main.tar.gz"
readonly TEMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf -- "${TEMP_DIR}"
}
trap cleanup EXIT

archive_path="${TEMP_DIR}/gitman.tar.gz"
source_root="${TEMP_DIR}/source"

curl --fail --silent --show-error --location \
  --proto '=https' --tlsv1.2 \
  "${ARCHIVE_URL}" --output "${archive_path}"

archive_listing="$(tar -tzf "${archive_path}")"
while IFS= read -r archive_member; do
  case "${archive_member}" in
    /*|..|../*|*/../*|*/..)
      echo "Unsafe path in downloaded archive: ${archive_member}" >&2
      exit 1
      ;;
  esac
done <<< "${archive_listing}"

mkdir -p -- "${source_root}"
tar --extract --gzip --file "${archive_path}" --directory "${source_root}"

gitman_dir="$(find "${source_root}" -mindepth 1 -maxdepth 1 -type d -name 'gitman-*' -print -quit)"
if [[ -z "${gitman_dir}" || ! -f "${gitman_dir}/install.sh" ]]; then
  echo "Unable to locate gitman install.sh in the downloaded source." >&2
  exit 1
fi

bash "${gitman_dir}/install.sh"
