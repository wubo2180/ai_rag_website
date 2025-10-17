@echo off
chcp 65001
echo ==========================================
echo   AI RAG Website - 快速启动脚本
echo   AI_UI_928_2 集成版
echo ==========================================
echo.

echo 🔄 检查环境...
cd /d E:\document\python_workspace\ai_rag_website\backend

echo 📊 应用数据库迁移...
D:\program\miniconda3\Scripts\conda.exe run -p D:\program\miniconda3 --no-capture-output python manage.py migrate

echo 🔍 检查Django配置...
D:\program\miniconda3\Scripts\conda.exe run -p D:\program\miniconda3 --no-capture-output python manage.py check

echo ✅ 环境检查完成！

echo.
echo 🚀 启动Django后端服务器 (端口 8000)...
echo 💡 访问地址: http://127.0.0.1:8000
echo 📝 API文档: http://127.0.0.1:8000/admin/
echo.
echo 💡 增强功能API测试:
echo    📡 模型列表: http://127.0.0.1:8000/api/chat/api/enhanced-models/
echo    🔗 相关推荐: http://127.0.0.1:8000/api/chat/api/suggestions/
echo.
echo 🛑 按 Ctrl+C 停止服务器
echo ==========================================
echo.

D:\program\miniconda3\Scripts\conda.exe run -p D:\program\miniconda3 --no-capture-output python manage.py runserver

echo.
echo 👋 Django服务器已停止
pause