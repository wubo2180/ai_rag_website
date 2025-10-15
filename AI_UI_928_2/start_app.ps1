# Vue + Flask 本地部署脚本
Write-Host "正在启动 Vue + Flask 应用..." -ForegroundColor Green

# 检查Python是否安装
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python版本: $pythonVersion" -ForegroundColor Yellow
} catch {
    Write-Host "错误: 未找到Python，请先安装Python" -ForegroundColor Red
    exit 1
}

# 检查Node.js是否安装
try {
    $nodeVersion = node --version 2>&1
    Write-Host "Node.js版本: $nodeVersion" -ForegroundColor Yellow
} catch {
    Write-Host "错误: 未找到Node.js，请先安装Node.js" -ForegroundColor Red
    exit 1
}

# 启动后端Flask服务器
Write-Host "正在启动Flask后端服务器..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; Write-Host 'Flask服务器启动中...' -ForegroundColor Green; python app.py"

# 等待后端启动
Start-Sleep -Seconds 3

# 启动前端Vue开发服务器
Write-Host "正在启动Vue前端开发服务器..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; Write-Host 'Vue开发服务器启动中...' -ForegroundColor Green; npm run dev"

# 等待前端启动
Start-Sleep -Seconds 5

Write-Host "应用启动完成！" -ForegroundColor Green
Write-Host "前端地址: http://localhost:5173" -ForegroundColor Yellow
Write-Host "后端地址: http://localhost:5000" -ForegroundColor Yellow

# 打开浏览器
Write-Host "正在打开浏览器..." -ForegroundColor Cyan
Start-Process "http://localhost:5173"

Write-Host "部署完成! 按任意键退出..." -ForegroundColor Green
Read-Host