#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="${CAD_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
RAG_PORT="${RAG_PORT:-8001}"
CONDA_ENV="${CONDA_ENV:-cad}"

if [[ -n "${CONDA_EXE:-}" ]]; then
  CONDA_CMD="$CONDA_EXE"
else
  CONDA_CMD="$(command -v conda || true)"
fi

if [[ -z "${CONDA_CMD}" ]]; then
  echo "conda was not found. Create/use the unified environment with: conda env create -f environment.yml"
  exit 1
fi

start_service() {
  local name="$1"
  local app_dir="$2"
  local port="$3"

  if port_is_open "$port"; then
    echo "${name} already appears to be running on http://${HOST}:${port}; reusing it."
    return 0
  fi

  echo "Starting ${name} on http://${HOST}:${port}"
  (
    cd "$ROOT_DIR"
    "$CONDA_CMD" run --no-capture-output -n "$CONDA_ENV" \
      python -m uvicorn app.main:app \
      --app-dir "$app_dir" \
      --host "$HOST" \
      --port "$port" \
      --reload
  ) &
  PIDS+=("$!")
}

port_is_open() {
  local port="$1"
  timeout 1 bash -c "</dev/tcp/${HOST}/${port}" >/dev/null 2>&1
}

PIDS=()

cleanup() {
  for pid in "${PIDS[@]:-}"; do
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
  done
}

trap cleanup EXIT INT TERM

start_service "CadArena backend" "backend" "$BACKEND_PORT"
start_service "CadArena RAG" "RAG" "$RAG_PORT"

echo "Backend and RAG are running from conda env '${CONDA_ENV}'. Press Ctrl+C to stop both."
if (( ${#PIDS[@]} == 0 )); then
  echo "Both services were already running."
  exit 0
fi

wait -n "${PIDS[@]}"
