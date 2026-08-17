#!/usr/bin/env bash
set -euo pipefail

APP_NAME="gitman"
MIN_PYTHON="3.11"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}"
INSTALL_DIR="${DATA_HOME}/${APP_NAME}"
VENV_DIR="${INSTALL_DIR}/venv"
BIN_DIR="${HOME}/.local/bin"
BIN_PATH="${BIN_DIR}/${APP_NAME}"

info() { printf '[INFO] %s\n' "$*"; }
success() { printf '[OK] %s\n' "$*"; }
warn() { printf '[WARN] %s\n' "$*" >&2; }
err() { printf '[ERROR] %s\n' "$*" >&2; }

find_python() {
  local candidates=(python3.13 python3.12 python3.11 python3)
  local candidate
  for candidate in "${candidates[@]}"; do
    if command -v "$candidate" >/dev/null 2>&1; then
      if "$candidate" - <<PY
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
      then
        command -v "$candidate"
        return 0
      fi
    fi
  done
  return 1
}

uninstall() {
  info "Uninstalling ${APP_NAME}"
  if [[ -L "$BIN_PATH" || -f "$BIN_PATH" ]]; then
    rm -f "$BIN_PATH"
    success "Removed ${BIN_PATH}"
  fi
  if [[ -d "$INSTALL_DIR" ]]; then
    rm -rf "$INSTALL_DIR"
    success "Removed ${INSTALL_DIR}"
  fi
}

if [[ "${1:-}" == "uninstall" ]]; then
  uninstall
  exit 0
fi

if ! command -v uv >/dev/null 2>&1; then
  err "Missing prerequisite: uv"
  warn "Install uv from https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
fi

PYTHON_BIN="$(find_python || true)"
if [[ -z "$PYTHON_BIN" ]]; then
  err "Missing prerequisite: Python ${MIN_PYTHON}+"
  warn "Install Python with Homebrew, for example: brew install python@3.13"
  exit 1
fi

info "Using Python: ${PYTHON_BIN}"
info "Using uv: $(command -v uv)"
info "Using install venv: ${VENV_DIR}"

mkdir -p "$INSTALL_DIR" "$BIN_DIR"
cd "$SCRIPT_DIR"
uv sync
uv build --wheel --out-dir "$SCRIPT_DIR/dist"
WHEEL_PATH="$(find "$SCRIPT_DIR/dist" -maxdepth 1 -name 'gitman-*.whl' -print | sort | tail -n 1)"
if [[ -z "$WHEEL_PATH" ]]; then
  err "Could not find built wheel under ${SCRIPT_DIR}/dist"
  exit 1
fi

uv venv "$VENV_DIR" --python "$PYTHON_BIN"
uv pip install --python "${VENV_DIR}/bin/python" --force-reinstall "$WHEEL_PATH"

cat > "$BIN_PATH" <<EOF
#!/usr/bin/env bash
export GITMAN_DEFAULT_REPO="\$PWD"
exec "${VENV_DIR}/bin/gitman" "\$@"
EOF
chmod +x "$BIN_PATH"

success "Installed ${APP_NAME} at ${BIN_PATH}"
info "Verify with: ${APP_NAME} --help"

case ":${PATH}:" in
  *":${BIN_DIR}:"*) ;;
  *)
    warn "${BIN_DIR} is not in PATH."
    warn "Add this line to your shell profile: export PATH=\"${BIN_DIR}:\$PATH\""
    ;;
esac
