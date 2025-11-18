@echo off
REM ==========================================
REM Git 仓库清理脚本
REM 用途: 从 Git 历史中移除不应该被追踪的文件
REM 注意: 此操作会修改 Git 历史,请谨慎使用
REM ==========================================

echo ================================================
echo Git 仓库清理工具
echo ================================================
echo.
echo 此脚本将从 Git 仓库中移除以下文件:
echo - 环境变量文件 (.env, .env.dev)
echo - node_modules 目录
echo - Python 缓存文件 (__pycache__, *.pyc)
echo - 其他 .gitignore 中定义的文件
echo.
echo 警告: 此操作会修改 Git 历史!
echo 建议在执行前先备份项目!
echo.
pause

echo.
echo [1/6] 检查当前 Git 状态...
git status

echo.
echo [2/6] 从 Git 索引中移除 .env 文件...
git rm --cached backend/.env 2>nul
git rm --cached backend/.env.dev 2>nul
git rm --cached backend/.env.prod 2>nul
git rm --cached .env 2>nul
git rm --cached .env.dev 2>nul
git rm --cached .env.prod 2>nul

echo.
echo [3/6] 从 Git 索引中移除 node_modules...
echo 这可能需要几分钟时间,请耐心等待...
git rm -r --cached frontend/node_modules 2>nul

echo.
echo [4/6] 从 Git 索引中移除 Python 缓存文件...
git rm -r --cached backend/__pycache__ 2>nul
for /r backend %%i in (__pycache__) do (
    git rm -r --cached "%%i" 2>nul
)

echo.
echo [5/6] 从 Git 索引中移除其他常见文件...
git rm -r --cached backend/.venv 2>nul
git rm --cached backend/db.sqlite3 2>nul
git rm -r --cached backend/logs 2>nul
git rm -r --cached backend/media 2>nul
git rm -r --cached backend/staticfiles 2>nul
git rm -r --cached frontend/dist 2>nul
git rm -r --cached frontend/.vscode 2>nul
git rm --cached *.log 2>nul
git rm --cached *.tmp 2>nul

echo.
echo [6/6] 检查清理后的状态...
git status

echo.
echo ================================================
echo 清理完成!
echo ================================================
echo.
echo 下一步操作:
echo 1. 检查上面的 git status 输出,确认要删除的文件
echo 2. 提交更改: git commit -m "清理不必要的文件和敏感信息"
echo 3. 推送到远程仓库: git push origin dev_yang
echo.
echo 注意事项:
echo - 本地文件不会被删除,只是不再被 Git 追踪
echo - .env 文件等敏感信息将从 Git 历史中移除
echo - 其他团队成员需要重新克隆或清理本地仓库
echo.
pause
