#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
RAG_DIR="$ROOT_DIR/RAG"
FRONTEND_DIR="$ROOT_DIR/frontend"

BACKEND_ENV_NAME="${BACKEND_ENV_NAME:-cad}"
RAG_ENV_NAME="${RAG_ENV_NAME:-rag-app}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
RAG_PORT="${RAG_PORT:-8001}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

has_command() {
  command -v "$1" >/dev/null 2>&1
}

assert_conda_env_exists() {
  local env_name="$1"
  if ! conda env list | awk 'NR > 2 {print $1}' | sed 's/*$//' | awk -v env="$env_name" '$0 == env {found=1} END {exit !found}'; then
    echo "Conda environment '$env_name' is not available." >&2
    echo "Create it first, then retry." >&2
    exit 1
  fi
}

is_port_busy() {
  local port="$1"
  python - "$port" <<'PY'
import socket
import sys

port = int(sys.argv[1])
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(0.4)
try:
    sock.connect(("127.0.0.1", port))
except OSError:
    print("0")
else:
    print("1")
finally:
    sock.close()
PY
}

cleanup_children() {
  if [[ "${#PIDS[@]}" -eq 0 ]]; then
    return
  fi
  echo
  echo "Stopping local services..."
  kill "${PIDS[@]}" 2>/dev/null || true
}

if ! has_command conda; then
  echo "conda is required but was not found in PATH." >&2
  exit 1
fi
if ! has_command npm; then
  echo "npm is required but was not found in PATH." >&2
  exit 1
fi

assert_conda_env_exists "$BACKEND_ENV_NAME"
assert_conda_env_exists "$RAG_ENV_NAME"

mkdir -p "$BACKEND_DIR/data" "$RAG_DIR/data"
export CADARENA_WORKSPACE_DB_PATH="$BACKEND_DIR/data/workspace.db"

PIDS=()
trap cleanup_children EXIT INT TERM

backend_busy="$(is_port_busy "$BACKEND_PORT")"
if [[ "$backend_busy" == "1" ]]; then
  echo "Backend already running on port $BACKEND_PORT. Reusing existing process."
else
  echo "Starting backend on :$BACKEND_PORT using conda env '$BACKEND_ENV_NAME'..."
  (
    cd "$BACKEND_DIR"
    conda run --no-capture-output -n "$BACKEND_ENV_NAME" \
      uvicorn app.main:app --reload --host 0.0.0.0 --port "$BACKEND_PORT"
  ) &
  PIDS+=("$!")
fi

rag_busy="$(is_port_busy "$RAG_PORT")"
if [[ "$rag_busy" == "1" ]]; then
  echo "RAG already running on port $RAG_PORT. Reusing existing process."
else
  echo "Starting RAG on :$RAG_PORT using conda env '$RAG_ENV_NAME'..."
  (
    cd "$RAG_DIR"
    conda run --no-capture-output -n "$RAG_ENV_NAME" \
      uvicorn app.main:app --reload --host 0.0.0.0 --port "$RAG_PORT"
  ) &
  PIDS+=("$!")
fi

frontend_busy="$(is_port_busy "$FRONTEND_PORT")"
if [[ "$frontend_busy" == "1" ]]; then
  echo "Frontend already running on port $FRONTEND_PORT. Reusing existing process."
else
  echo "Starting frontend on :$FRONTEND_PORT..."
  (
    cd "$FRONTEND_DIR"
    PORT="$FRONTEND_PORT" npm start
  ) &
  PIDS+=("$!")
fi

if [[ "${#PIDS[@]}" -eq 0 ]]; then
  echo "Nothing to start. Backend, RAG, and Frontend are already up."
  exit 0
fi

echo "Services started (backend + RAG + frontend). Press Ctrl+C to stop processes started by this script."
wait -n "${PIDS[@]}"
