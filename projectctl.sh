#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
PID_DIR="${LOG_DIR}/pids"
mkdir -p "${LOG_DIR}" "${PID_DIR}"

BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"
FRONTEND_PORT="${FRONTEND_PORT:-3001}"
COMMISSION_HOST="${COMMISSION_HOST:-0.0.0.0}"
COMMISSION_PORT="${COMMISSION_PORT:-6001}"
PAPER_HOST="${PAPER_HOST:-0.0.0.0}"
PAPER_PORT="${PAPER_PORT:-6002}"

PYTHON_BIN="${PYTHON_BIN:-/home/xjlab/miniconda3/bin/python}"
COMMISSION_PYTHON="${COMMISSION_PYTHON:-${ROOT_DIR}/IBoxTech-ocr-commission/venv/bin/python}"
NPM_BIN="${NPM_BIN:-$(command -v npm || true)}"
WAIT_SECONDS="${WAIT_SECONDS:-45}"

BACKEND_HEALTH="http://127.0.0.1:${BACKEND_PORT}/api/ocr/health"
FRONTEND_HEALTH="http://127.0.0.1:${FRONTEND_PORT}/"
COMMISSION_HEALTH="http://127.0.0.1:${COMMISSION_PORT}/health"
PAPER_HEALTH="http://127.0.0.1:${PAPER_PORT}/health"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

read_env_value() {
  local key="$1"
  local file="$2"
  [ -f "${file}" ] || return 0
  grep -E "^[[:space:]]*${key}[[:space:]]*=" "${file}" \
    | tail -n 1 \
    | sed -E "s/^[^=]+=//; s/^[[:space:]]+//; s/[[:space:]]+$//; s/^['\"]//; s/['\"]$//" \
    | tr -d '\r'
}

DIFY_API_URL="${DIFY_API_URL:-$(read_env_value DIFY_API_URL "${ROOT_DIR}/backend/.env")}" 
DIFY_HEALTH_URL="${DIFY_HEALTH_URL:-}"
if [ -z "${DIFY_HEALTH_URL}" ] && [ -n "${DIFY_API_URL}" ]; then
  DIFY_HEALTH_URL="${DIFY_API_URL%/v1}/console/api/setup"
fi

check_url() {
  local url="$1"
  curl -fsS --max-time 8 "${url}" >/dev/null 2>&1
}

listener_pids() {
  local port="$1"
  ss -ltnp 2>/dev/null \
    | awk -v suffix=":${port}" '$4 ~ suffix"$" {print}' \
    | sed -nE 's/.*pid=([0-9]+).*/\1/p' \
    | sort -u
}

port_in_use() {
  local port="$1"
  ss -ltn 2>/dev/null | awk -v suffix=":${port}" '$4 ~ suffix"$" {found=1} END {exit found ? 0 : 1}'
}

pid_alive() {
  local pid="$1"
  [ -n "${pid}" ] && ps -p "${pid}" >/dev/null 2>&1
}

pid_from_file() {
  local pidfile="$1"
  [ -f "${pidfile}" ] || return 0
  tr -cd '0-9' < "${pidfile}"
}

adopt_listener_pid() {
  local pidfile="$1"
  local port="$2"
  local pid
  pid="$(listener_pids "${port}" | head -n 1 || true)"
  if [ -n "${pid}" ]; then
    echo "${pid}" > "${pidfile}"
  fi
}

collect_service_pids() {
  local pidfile="$1"
  local port="$2"
  local file_pid
  file_pid="$(pid_from_file "${pidfile}" || true)"
  {
    if [ -n "${file_pid}" ] && pid_alive "${file_pid}"; then
      echo "${file_pid}"
    fi
    listener_pids "${port}" || true
  } | sort -u
}

wait_for_health() {
  local name="$1"
  local health_url="$2"
  local seconds="${3:-${WAIT_SECONDS}}"
  local elapsed=0

  while [ "${elapsed}" -lt "${seconds}" ]; do
    if check_url "${health_url}"; then
      log "${name} is healthy: ${health_url}"
      return 0
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done

  log "WARN: ${name} did not become healthy within ${seconds}s: ${health_url}"
  return 1
}

start_service() {
  local name="$1"
  local cwd="$2"
  local pidfile="$3"
  local logfile="$4"
  local port="$5"
  local health_url="$6"
  shift 6

  mkdir -p "$(dirname "${pidfile}")" "$(dirname "${logfile}")"

  if check_url "${health_url}"; then
    adopt_listener_pid "${pidfile}" "${port}"
    log "${name} already healthy on port ${port}"
    return 0
  fi

  local old_pid
  old_pid="$(pid_from_file "${pidfile}" || true)"
  if [ -n "${old_pid}" ] && ! pid_alive "${old_pid}"; then
    rm -f "${pidfile}"
  fi

  if port_in_use "${port}"; then
    adopt_listener_pid "${pidfile}" "${port}"
    log "WARN: ${name} port ${port} is already in use, skip starting. Check ${logfile} or run status."
    return 1
  fi

  log "starting ${name} ..."
  (
    cd "${cwd}"
    nohup "$@" > "${logfile}" 2>&1 < /dev/null &
    echo $! > "${pidfile}"
  )

  sleep 1
  wait_for_health "${name}" "${health_url}" "${WAIT_SECONDS}" || true
}

stop_service() {
  local name="$1"
  local pidfile="$2"
  local port="$3"
  local pids
  pids="$(collect_service_pids "${pidfile}" "${port}" || true)"

  if [ -z "${pids}" ]; then
    rm -f "${pidfile}"
    log "${name} is not running"
    return 0
  fi

  log "stopping ${name}: ${pids}"
  for pid in ${pids}; do
    kill "${pid}" 2>/dev/null || true
  done

  local waited=0
  while [ "${waited}" -lt 12 ]; do
    local alive=""
    for pid in ${pids}; do
      if pid_alive "${pid}"; then
        alive="${alive} ${pid}"
      fi
    done
    [ -z "${alive}" ] && break
    sleep 1
    waited=$((waited + 1))
  done

  for pid in ${pids}; do
    if pid_alive "${pid}"; then
      log "force killing ${name} pid ${pid}"
      kill -9 "${pid}" 2>/dev/null || true
    fi
  done
  rm -f "${pidfile}"
}

status_service() {
  local name="$1"
  local pidfile="$2"
  local port="$3"
  local health_url="$4"
  local logfile="$5"
  local pids health
  pids="$(collect_service_pids "${pidfile}" "${port}" | paste -sd, - || true)"
  [ -n "${pids}" ] || pids="-"
  if check_url "${health_url}"; then
    health="ok"
    adopt_listener_pid "${pidfile}" "${port}"
  else
    health="down"
  fi
  printf '%-16s port=%-5s health=%-5s pid=%-16s log=%s\n' "${name}" "${port}" "${health}" "${pids}" "${logfile}"
}

start_all() {
  if [ ! -x "${PYTHON_BIN}" ]; then
    log "ERROR: PYTHON_BIN not executable: ${PYTHON_BIN}"
    exit 1
  fi
  if [ ! -x "${COMMISSION_PYTHON}" ]; then
    log "WARN: commission venv python not found, fallback to ${PYTHON_BIN}"
    COMMISSION_PYTHON="${PYTHON_BIN}"
  fi
  if [ -z "${NPM_BIN}" ]; then
    log "ERROR: npm not found. Set NPM_BIN=/path/to/npm and retry."
    exit 1
  fi

  local commission_pythonpath="${ROOT_DIR}/IBoxTech-ocr-commission"
  local paper_pythonpath="${ROOT_DIR}/IBoxTech-ocr-paper"
  if [ -n "${PYTHONPATH:-}" ]; then
    commission_pythonpath="${commission_pythonpath}:${PYTHONPATH}"
    paper_pythonpath="${paper_pythonpath}:${PYTHONPATH}"
  fi

  start_service \
    "ocr-commission" \
    "${ROOT_DIR}/IBoxTech-ocr-commission" \
    "${PID_DIR}/ocr-commission.pid" \
    "${LOG_DIR}/ocr-commission.log" \
    "${COMMISSION_PORT}" \
    "${COMMISSION_HEALTH}" \
    env PYTHONPATH="${commission_pythonpath}" "${COMMISSION_PYTHON}" api_server.py

  start_service \
    "ocr-paper" \
    "${ROOT_DIR}/IBoxTech-ocr-paper" \
    "${PID_DIR}/ocr-paper.pid" \
    "${LOG_DIR}/ocr-paper.log" \
    "${PAPER_PORT}" \
    "${PAPER_HEALTH}" \
    env PYTHONPATH="${paper_pythonpath}" "${PYTHON_BIN}" -m uvicorn api_server:app --host "${PAPER_HOST}" --port "${PAPER_PORT}"

  start_service \
    "backend" \
    "${ROOT_DIR}/backend" \
    "${PID_DIR}/backend.pid" \
    "${LOG_DIR}/backend-runserver.log" \
    "${BACKEND_PORT}" \
    "${BACKEND_HEALTH}" \
    "${PYTHON_BIN}" manage.py runserver "${BACKEND_HOST}:${BACKEND_PORT}" --noreload

  start_service \
    "frontend" \
    "${ROOT_DIR}/frontend" \
    "${PID_DIR}/frontend.pid" \
    "${LOG_DIR}/frontend-vite.log" \
    "${FRONTEND_PORT}" \
    "${FRONTEND_HEALTH}" \
    "${NPM_BIN}" run dev -- --host "${FRONTEND_HOST}" --port "${FRONTEND_PORT}" --strictPort

  status_all
}

stop_all() {
  stop_service "frontend" "${PID_DIR}/frontend.pid" "${FRONTEND_PORT}"
  stop_service "backend" "${PID_DIR}/backend.pid" "${BACKEND_PORT}"
  stop_service "ocr-paper" "${PID_DIR}/ocr-paper.pid" "${PAPER_PORT}"
  stop_service "ocr-commission" "${PID_DIR}/ocr-commission.pid" "${COMMISSION_PORT}"
}

status_all() {
  status_service "ocr-commission" "${PID_DIR}/ocr-commission.pid" "${COMMISSION_PORT}" "${COMMISSION_HEALTH}" "${LOG_DIR}/ocr-commission.log"
  status_service "ocr-paper" "${PID_DIR}/ocr-paper.pid" "${PAPER_PORT}" "${PAPER_HEALTH}" "${LOG_DIR}/ocr-paper.log"
  status_service "backend" "${PID_DIR}/backend.pid" "${BACKEND_PORT}" "${BACKEND_HEALTH}" "${LOG_DIR}/backend-runserver.log"
  status_service "frontend" "${PID_DIR}/frontend.pid" "${FRONTEND_PORT}" "${FRONTEND_HEALTH}" "${LOG_DIR}/frontend-vite.log"
  if [ -n "${DIFY_HEALTH_URL}" ]; then
    if check_url "${DIFY_HEALTH_URL}"; then
      printf '%-16s health=%-5s url=%s\n' "dify-external" "ok" "${DIFY_HEALTH_URL}"
    else
      printf '%-16s health=%-5s url=%s\n' "dify-external" "down" "${DIFY_HEALTH_URL}"
    fi
  fi
}

show_logs() {
  local service="${1:-}"
  local logfile=""
  case "${service}" in
    commission|ocr-commission) logfile="${LOG_DIR}/ocr-commission.log" ;;
    paper|ocr-paper) logfile="${LOG_DIR}/ocr-paper.log" ;;
    backend) logfile="${LOG_DIR}/backend-runserver.log" ;;
    frontend) logfile="${LOG_DIR}/frontend-vite.log" ;;
    *)
      echo "Usage: $0 logs {backend|frontend|commission|paper}"
      exit 1
      ;;
  esac
  mkdir -p "$(dirname "${logfile}")"
  touch "${logfile}"
  tail -n 120 -f "${logfile}"
}

usage() {
  cat <<EOF
Usage: $(basename "$0") {start|stop|restart|status|logs SERVICE}

Services managed:
  ocr-commission  http://127.0.0.1:${COMMISSION_PORT}/health
  ocr-paper       http://127.0.0.1:${PAPER_PORT}/health
  backend         http://127.0.0.1:${BACKEND_PORT}/api/ocr/health
  frontend        http://172.21.108.102:${FRONTEND_PORT}/

Common commands:
  ./start.sh
  ./status.sh
  ./stop.sh
  ./restart.sh
  ./projectctl.sh logs backend
EOF
}

case "${1:-start}" in
  start) start_all ;;
  stop) stop_all ;;
  restart) stop_all; start_all ;;
  status) status_all ;;
  logs) shift; show_logs "${1:-}" ;;
  help|-h|--help) usage ;;
  *) usage; exit 1 ;;
esac
