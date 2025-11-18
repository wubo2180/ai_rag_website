@echo off
chcp 65001 > nul
echo ========================================
echo 清理被错误追踪的文件
echo ========================================
echo.

echo 这个脚本将从 Git 中移除以下不应该被追踪的文件:
echo - backend/__pycache__/ (Python 缓存)
echo - backend/.venv/ (虚拟环境)
echo - frontend/node_modules/ (Node.js 依赖)
echo.
echo 警告: 这些文件将从 Git 中移除，但保留在本地!
echo.
pause

echo.
echo [1/6] 移除 Python 缓存文件 (__pycache__)...
git rm -r --cached backend/**/__pycache__ 2>nul
git rm -r --cached backend/apps/accounts/__pycache__ 2>nul
echo ✓ 完成

echo.
echo [2/6] 移除虚拟环境 (.venv)...
git rm -r --cached backend/.venv 2>nul
echo ✓ 完成

echo.
echo [3/6] 移除 Node.js 依赖 (node_modules)...
git rm -r --cached frontend/node_modules 2>nul
echo ✓ 完成

echo.
echo [4/6] 移除 .vite 缓存...
git rm -r --cached frontend/node_modules/.vite 2>nul
echo ✓ 完成

echo.
echo [5/6] 检查状态...
git status --short

echo.
echo [6/6] 提交更改...
set /p "confirm=是否提交这些更改？(Y/N): "
if /i "%confirm%"=="Y" (
    git commit -m "🧹 从 Git 中移除不应该被追踪的文件 (pycache, venv, node_modules)"
    echo.
    echo ✅ 提交成功!
    echo.
    echo 下一步: 推送到远程仓库
    echo 命令: git push origin main
) else (
    echo.
    echo ❌ 已取消提交
    echo 可以使用 'git reset HEAD' 撤销更改
)

echo.
pause
