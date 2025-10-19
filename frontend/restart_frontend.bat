@echo off
chcp 65001
echo ========================================
echo 重启前端服务以加载 ECharts
echo ========================================
echo.
echo 正在切换到前端目录...
cd /d e:\document\python_workspace\ai_rag_website\frontend

echo.
echo 已安装的 ECharts 版本:
npm list echarts

echo.
echo 启动开发服务器...
echo 访问地址: http://localhost:5173/knowledge-graph
echo.
npm run dev

pause
