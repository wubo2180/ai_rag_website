@echo off
REM ASGI 生产环境启动脚本
REM 使用 Gunicorn + Uvicorn workers 部署

echo 启动 AI RAG Website - ASGI 服务器 (生产模式)...
echo ================================================

REM 设置环境变量
set DJANGO_SETTINGS_MODULE=config.settings
set PYTHONPATH=%PYTHONPATH%;%cd%

REM 启动 ASGI 服务器
echo 使用 Gunicorn + Uvicorn workers...
gunicorn config.asgi:application ^
    --bind 0.0.0.0:8000 ^
    --workers 4 ^
    --worker-class uvicorn.workers.UvicornWorker ^
    --worker-connections 1000 ^
    --max-requests 1000 ^
    --max-requests-jitter 100 ^
    --timeout 120 ^
    --keep-alive 2 ^
    --access-logfile - ^
    --error-logfile - ^
    --log-level info ^
    --reload

echo.
echo 服务器已启动: http://0.0.0.0:8000/
echo 按任意键停止服务器...
pause