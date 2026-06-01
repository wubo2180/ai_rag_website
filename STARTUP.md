# Startup

This project root contains a unified service controller for the current deployment on `172.21.108.102`.

## Common Commands

```bash
cd /home/xjlab/zhy/all-anbos/ai_rag_website
./start.sh
./status.sh
./stop.sh
./restart.sh
```

You can also call the controller directly:

```bash
./projectctl.sh start
./projectctl.sh status
./projectctl.sh logs backend
./projectctl.sh logs frontend
./projectctl.sh logs commission
./projectctl.sh logs paper
```

## Managed Services

| Service | Port | Health check | Log |
| --- | ---: | --- | --- |
| OCR commission | 6001 | `http://127.0.0.1:6001/health` | `logs/ocr-commission.log` |
| OCR paper | 6002 | `http://127.0.0.1:6002/health` | `logs/ocr-paper.log` |
| Django backend | 8000 | `http://127.0.0.1:8000/api/ocr/health` | `logs/backend-runserver.log` |
| Vue frontend | 3001 | `http://127.0.0.1:3001/` | `logs/frontend-vite.log` |

Dify is treated as an external dependency and is not started by this project script. The controller reads `DIFY_API_URL` from `backend/.env` and checks the Dify setup endpoint during `status`.

## Overrides

The script supports environment overrides when needed:

```bash
BACKEND_PORT=8001 FRONTEND_PORT=3002 ./projectctl.sh start
PYTHON_BIN=/path/to/python NPM_BIN=/path/to/npm ./projectctl.sh start
```
