@echo off
echo ================================
echo   AI RAG 系统依赖安装脚本
echo ================================
echo.

cd /d "%~dp0"

echo [1/5] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或未添加到PATH，请先安装Python 3.8+
    pause
    exit /b 1
)

echo [2/5] 检查Node.js环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js未安装或未添加到PATH，请先安装Node.js 16+
    pause
    exit /b 1
)

echo [3/5] 安装后端依赖...
cd backend
if exist "requirements.txt" (
    pip install -r requirements.txt
) else (
    echo ⚠️  未找到requirements.txt文件
)

echo [4/5] 初始化数据库...
python manage.py makemigrations
python manage.py migrate

echo [5/5] 安装前端依赖...
cd ..\frontend
if exist "package.json" (
    npm install
) else (
    echo ⚠️  未找到package.json文件
)

echo.
echo ✅ 安装完成！
echo.
echo 📋 下一步:
echo   1. 运行 start_dev.bat 启动开发服务器
echo   2. 访问 http://localhost:3000/ 查看前端
echo   3. 访问 http://127.0.0.1:8000/admin/ 管理后台
echo.
echo 💡 创建管理员用户 (可选):
echo   cd backend
echo   python manage.py createsuperuser
echo.
pause