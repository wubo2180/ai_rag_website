@echo off
chcp 65001
echo ==========================================
echo   AI RAG Website - 前端启动脚本  
echo   Vue.js + AI_UI_928_2 增强界面
echo ==========================================
echo.

cd /d E:\document\python_workspace\ai_rag_website\frontend

echo 🔄 检查Node.js环境...
node --version
npm --version

echo.
echo 📦 安装/更新依赖包...
npm install

echo.
echo 🚀 启动前端开发服务器 (端口 3000)...
echo 💡 访问地址: http://localhost:3000
echo.
echo 🎯 可用路由:
echo    🏠 首页:       http://localhost:3000/
echo    💬 基础聊天:   http://localhost:3000/chat  
echo    🧠 智能对话:   http://localhost:3000/enhanced-chat
echo    📝 历史记录:   http://localhost:3000/sessions
echo    📁 文档管理:   http://localhost:3000/documents
echo    👤 个人资料:   http://localhost:3000/profile
echo.
echo 🛑 按 Ctrl+C 停止服务器
echo ==========================================
echo.

npm run dev

echo.
echo 👋 前端服务器已停止
pause