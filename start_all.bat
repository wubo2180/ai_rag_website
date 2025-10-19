@echo off
chcp 65001
echo ========================================
echo 启动 AI RAG 知识图谱系统
echo ========================================

echo.
echo [1/2] 启动后端服务 (Django)...
cd /d e:\document\python_workspace\ai_rag_website\backend
start "Django Backend" cmd /k "python manage.py runserver"

timeout /t 3 /nobreak >nul

echo.
echo [2/2] 启动前端服务 (Vue + Vite)...
cd /d e:\document\python_workspace\ai_rag_website\frontend
start "Vue Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo 服务启动完成！
echo ========================================
echo.
echo 后端地址: http://localhost:8000
echo 前端地址: http://localhost:5173
echo.
echo 知识图谱API: http://localhost:8000/api/kg/
echo 完整图谱数据: http://localhost:8000/api/kg/graph/full_graph/
echo.
echo 按任意键关闭此窗口...
pause >nul
