@echo off
REM ASGI 开发环境启动脚本
REM 使用 Uvicorn 直接启动，支持热重载

echo 启动 AI RAG Website - ASGI 服务器 (开发模式)...
echo ===============================================

REM 设置环境变量
set DJANGO_SETTINGS_MODULE=config.settings
set PYTHONPATH=%PYTHONPATH%;%cd%

REM 启动开发服务器
echo 使用 Uvicorn 开发服务器...
uvicorn config.asgi:application ^
    --host 0.0.0.0 ^
    --port 8000 ^
    --reload ^
    --reload-dir . ^
    --log-level debug ^
    --access-log

echo.
echo 开发服务器已启动: http://localhost:8000/
echo 按任意键停止服务器...
pause