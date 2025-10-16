# AI RAG 智能问答系统启动脚本
Write-Host "================================" -ForegroundColor Cyan
Write-Host "    AI RAG 智能问答系统启动" -ForegroundColor Cyan  
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 获取脚本所在目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "[1/4] 检查目录结构..." -ForegroundColor Yellow

# 检查后端文件
if (-not (Test-Path "backend\manage.py")) {
    Write-Host "❌ 错误: 未找到后端文件，请确认在正确目录下运行" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

# 检查前端文件  
if (-not (Test-Path "frontend\package.json")) {
    Write-Host "❌ 错误: 未找到前端文件，请确认在正确目录下运行" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

Write-Host "[2/4] 启动后端服务..." -ForegroundColor Yellow

# 启动后端服务
$BackendJob = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "Set-Location '$ScriptDir\backend'; python manage.py runserver" -PassThru

Write-Host "[3/4] 等待后端启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "[4/4] 启动前端服务..." -ForegroundColor Yellow

# 启动前端服务
$FrontendJob = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "Set-Location '$ScriptDir\frontend'; npm run dev" -PassThru

Write-Host ""
Write-Host "✅ 启动完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📖 访问地址:" -ForegroundColor Cyan
Write-Host "   前端开发环境: http://localhost:3000/" -ForegroundColor White
Write-Host "   后端API服务:  http://127.0.0.1:8000/" -ForegroundColor White  
Write-Host "   管理后台:     http://127.0.0.1:8000/admin/" -ForegroundColor White
Write-Host ""
Write-Host "💡 提示:" -ForegroundColor Cyan
Write-Host "   - 两个PowerShell窗口将自动打开" -ForegroundColor Gray
Write-Host "   - 关闭窗口即可停止对应服务" -ForegroundColor Gray
Write-Host "   - 首次运行前请确保已安装依赖" -ForegroundColor Gray
Write-Host ""

Read-Host "按任意键退出此窗口"