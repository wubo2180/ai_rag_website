#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/xjlab/zhy/all-anbos/ai_rag_website"
NGINX_PID="$ROOT/runtime/nginx-5173.pid"

stop_by_pid_file() {
    local name="$1"
    local pid_file="$2"
    if [ -f "$pid_file" ]; then
        local pid
        pid=$(cat "$pid_file" 2>/dev/null || true)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo "[stop] $name: $pid"
            kill "$pid" || true
            sleep 1
        fi
        rm -f "$pid_file"
    fi
}

stop_matching() {
    local name="$1"
    local pattern="$2"
    local pids
    pids=$(pgrep -u xjlab -f "$pattern" || true)
    if [ -n "$pids" ]; then
        echo "[stop] $name: $pids"
        kill $pids || true
        sleep 1
    else
        echo "[ok] $name not running"
    fi
}

stop_by_pid_file "frontend entry nginx" "$NGINX_PID"
stop_matching "Django main backend" "$ROOT/backend/manage.py runserver"
stop_matching "checker OCR API" "$ROOT/IBoxTech-ocrchecker/backend/venv/bin/python app.py"
stop_matching "paper OCR" "$ROOT/IBoxTech-ocr-paper/venv/bin/python api_server.py"
stop_matching "commission OCR" "$ROOT/IBoxTech-ocr-commission/venv/bin/python api_server.py"

echo "[done] ai_rag_website stack stopped"
