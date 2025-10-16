@echo off
echo ================================
echo    AI RAG 智能问答系统启动
echo ================================
echo.

cd /d "%~dp0"

echo [1/4] 检查目录结构...
if not exist "backend\manage.py" (
    echo 错误: 未找到后端文件，请确认在正确目录下运行
    pause
    exit /b 1
)

if not exist "frontend\package.json" (
    echo 错误: 未找到前端文件，请确认在正确目录下运行  
    pause
    exit /b 1
)

echo [2/4] 启动后端服务...
start "Django Backend" cmd /k "cd backend && python manage.py runserver"

echo [3/4] 等待后端启动...
timeout /t 5 /nobreak >nul

echo [4/4] 启动前端服务...
start "Vue Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ✅ 启动完成！
echo.
echo 📖 访问地址:
echo    前端开发环境: http://localhost:3000/
echo    后端API服务:  http://127.0.0.1:8000/
echo    管理后台:     http://127.0.0.1:8000/admin/
echo.
echo 💡 提示: 
echo    - 两个命令行窗口将自动打开
echo    - 关闭窗口即可停止对应服务
echo    - 首次运行前请确保已安装依赖
echo.
pause