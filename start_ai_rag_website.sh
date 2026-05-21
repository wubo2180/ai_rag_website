#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/xjlab/zhy/all-anbos/ai_rag_website"
LOG_DIR="$ROOT/logs"
RUNTIME_DIR="$ROOT/runtime"
NGINX_CONF="$ROOT/nginx-ai-rag-5173.conf"

mkdir -p "$LOG_DIR" "$RUNTIME_DIR"

is_port_listening() {
    ss -lnt 2>/dev/null | awk '{print $4}' | grep -Eq "[:.]$1$"
}

start_background_service() {
    local name="$1"
    local dir="$2"
    local port="$3"
    local log_file="$4"
    shift 4

    if is_port_listening "$port"; then
        echo "[ok] $name already listening on $port"
        return 0
    fi

    echo "[start] $name on $port"
    (
        cd "$dir"
        nohup "$@" > "$log_file" 2>&1 &
    )

    for _ in $(seq 1 20); do
        if is_port_listening "$port"; then
            echo "[ok] $name started"
            return 0
        fi
        sleep 1
    done

    echo "[error] $name did not start; see $log_file" >&2
    return 1
}

stop_old_checker_frontend_nginx() {
    local old_pids
    old_pids=$(pgrep -u xjlab -f 'nginx: master process nginx -p .*/IBoxTech-ocrchecker' || true)
    if [ -n "$old_pids" ]; then
        echo "[stop] old OCR checker frontend nginx: $old_pids"
        kill $old_pids || true
        sleep 1
    fi
}

start_background_service \
    "commission OCR" \
    "$ROOT/IBoxTech-ocr-commission" \
    6001 \
    "$LOG_DIR/ocr-commission.log" \
    "$ROOT/IBoxTech-ocr-commission/venv/bin/python" api_server.py

start_background_service \
    "paper OCR" \
    "$ROOT/IBoxTech-ocr-paper" \
    6002 \
    "$LOG_DIR/ocr-paper.log" \
    "$ROOT/IBoxTech-ocr-paper/venv/bin/python" api_server.py

start_background_service \
    "checker OCR API" \
    "$ROOT/IBoxTech-ocrchecker/backend" \
    5001 \
    "$LOG_DIR/ocr-checker.log" \
    "$ROOT/IBoxTech-ocrchecker/backend/venv/bin/python" app.py

start_background_service \
    "Django main backend" \
    "$ROOT/backend" \
    8000 \
    "$LOG_DIR/django-runserver.log" \
    "/home/xjlab/miniconda3/bin/python" manage.py runserver 127.0.0.1:8000

stop_old_checker_frontend_nginx

if is_port_listening 5173; then
    echo "[ok] frontend entry already listening on 5173"
else
    echo "[start] frontend entry nginx on 5173"
    nginx -p "$ROOT" -c "$NGINX_CONF"
fi

echo
echo "Access: http://172.21.108.102:5173/"
echo "OCR files: http://172.21.108.102:5173/ocr/files"
echo "Health: http://172.21.108.102:5173/api/ocr/checker/health"
