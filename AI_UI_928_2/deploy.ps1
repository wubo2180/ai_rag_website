# Vue + Flask Local Deployment Script
Write-Host "Starting Vue + Flask Application..." -ForegroundColor Green

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python Version: $pythonVersion" -ForegroundColor Yellow
} catch {
    Write-Host "Error: Python not found. Please install Python first." -ForegroundColor Red
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "Node.js Version: $nodeVersion" -ForegroundColor Yellow
} catch {
    Write-Host "Error: Node.js not found. Please install Node.js first." -ForegroundColor Red
    exit 1
}

# Start Flask Backend
Write-Host "Starting Flask Backend Server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; Write-Host 'Starting Flask Server...' -ForegroundColor Green; python app.py"

# Wait for backend to start
Start-Sleep -Seconds 3

# Start Vue Frontend
Write-Host "Starting Vue Frontend Server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; Write-Host 'Starting Vue Dev Server...' -ForegroundColor Green; npm run dev"

# Wait for frontend to start
Start-Sleep -Seconds 5

Write-Host "Application Started Successfully!" -ForegroundColor Green
Write-Host "Frontend URL: http://localhost:5173" -ForegroundColor Yellow
Write-Host "Backend URL: http://localhost:5000" -ForegroundColor Yellow

# Open Browser
Write-Host "Opening Browser..." -ForegroundColor Cyan
Start-Process "http://localhost:5173"

Write-Host "Deployment Complete! Press any key to exit..." -ForegroundColor Green
Read-Host