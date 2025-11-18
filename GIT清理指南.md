# Git 仓库清理指南

## 问题说明

虽然已经添加了 `.gitignore` 文件,但是 Git 不会自动删除**已经被追踪**的文件。这意味着:

- ✅ `.gitignore` 会阻止新文件被添加到 Git
- ❌ `.gitignore` **不会**删除已经在 Git 中的文件

## 当前问题

根据检查,您的仓库中已经追踪了以下不应该被追踪的文件:

### 🔴 敏感文件(高风险)
```
backend/.env
backend/.env.dev
```
**风险**: 可能包含数据库密码、API 密钥等敏感信息

### 📦 依赖包(大文件)
```
frontend/node_modules/  (数千个文件)
```
**影响**: 极大增加仓库大小,拖慢克隆速度

### 🗑️ 其他应忽略的文件
- Python 缓存: `__pycache__/`, `*.pyc`
- 虚拟环境: `.venv/`
- 数据库文件: `db.sqlite3`
- 日志文件: `*.log`
- 临时文件: `*.tmp`

## 解决方案

### 方案 1: 简单清理(推荐)

**适用场景**: 只需要让 Git 停止追踪这些文件,不需要完全删除历史记录

#### 步骤 1: 运行清理脚本

```cmd
cleanup_git.bat
```

或手动执行:

```cmd
# 移除 .env 文件
git rm --cached backend/.env
git rm --cached backend/.env.dev

# 移除 node_modules
git rm -r --cached frontend/node_modules

# 移除 Python 缓存
git rm -r --cached backend/__pycache__
```

#### 步骤 2: 提交更改

```cmd
git add .gitignore
git commit -m "清理不必要的文件,添加 .gitignore"
```

#### 步骤 3: 推送到远程

```cmd
git push origin dev_yang
```

### 方案 2: 彻底清理(高级)

**适用场景**: 需要从 Git 历史中完全删除敏感信息

**⚠️ 警告**: 此操作会重写 Git 历史!需要所有团队成员重新克隆仓库!

#### 使用 BFG Repo-Cleaner

```cmd
# 1. 下载 BFG
# https://rtyley.github.io/bfg-repo-cleaner/

# 2. 创建备份
git clone --mirror e:\document\python_workspace\ai_rag_website backup-repo.git

# 3. 删除敏感文件
java -jar bfg.jar --delete-files ".env" ai_rag_website
java -jar bfg.jar --delete-folders "node_modules" ai_rag_website

# 4. 清理和推送
cd ai_rag_website
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force
```

#### 使用 git filter-branch(Git 内置)

```cmd
# 删除 .env 文件历史
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch backend/.env backend/.env.dev" \
  --prune-empty --tag-name-filter cat -- --all

# 删除 node_modules 历史
git filter-branch --force --index-filter \
  "git rm -r --cached --ignore-unmatch frontend/node_modules" \
  --prune-empty --tag-name-filter cat -- --all

# 清理
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 强制推送
git push origin --force --all
```

## 操作步骤(推荐流程)

### 第 1 步: 备份

```cmd
# 创建项目备份
cd e:\document\python_workspace
xcopy ai_rag_website ai_rag_website_backup /E /I /H
```

### 第 2 步: 运行清理脚本

```cmd
cd e:\document\python_workspace\ai_rag_website
cleanup_git.bat
```

### 第 3 步: 检查清理结果

```cmd
git status
```

您应该看到:
```
Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
        deleted:    backend/.env
        deleted:    backend/.env.dev
        deleted:    frontend/node_modules/...
        ...
```

### 第 4 步: 提交并推送

```cmd
git commit -m "🧹 清理敏感文件和不必要的依赖

- 移除 .env 文件避免泄露敏感信息
- 移除 node_modules 减小仓库大小
- 添加完整的 .gitignore 配置"

git push origin dev_yang
```

### 第 5 步: 验证远程仓库

访问 GitHub/GitLab,确认:
- ✅ `.gitignore` 已更新
- ✅ `.env` 文件不再显示
- ✅ `node_modules` 不再显示

## 注意事项

### ⚠️ 重要警告

1. **本地文件不会被删除**: `git rm --cached` 只是让 Git 停止追踪,文件仍然在本地
2. **历史记录仍然存在**: 简单清理不会删除历史中的文件
3. **敏感信息泄露**: 如果 `.env` 包含密码,建议:
   - 修改所有密码
   - 重新生成 API 密钥
   - 使用方案 2 完全清理历史

### 📝 其他团队成员需要做什么?

#### 方案 1(简单清理)后:
```cmd
git pull origin dev_yang
```

#### 方案 2(彻底清理)后:
```cmd
# 删除旧仓库
cd e:\document\python_workspace
rmdir /s /q ai_rag_website

# 重新克隆
git clone <仓库地址>
```

### 🔧 后续最佳实践

1. **创建 .env.example 模板**
   ```env
   # .env.example
   DATABASE_URL=postgresql://user:password@localhost/dbname
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ```

2. **在 README 中说明**
   ```markdown
   ## 环境配置
   1. 复制 `.env.example` 为 `.env`
   2. 修改 `.env` 中的配置
   3. 不要提交 `.env` 文件
   ```

3. **使用环境变量管理工具**
   - Python: `python-dotenv`
   - Node.js: `dotenv`

4. **定期检查**
   ```cmd
   git ls-files | findstr /I "\.env"
   git ls-files | findstr /I "node_modules"
   ```

## 常见问题

### Q: 为什么 .env 文件这么危险?
**A**: 通常包含:
- 数据库连接字符串(用户名/密码)
- API 密钥
- 加密密钥(SECRET_KEY)
- 第三方服务凭证

一旦泄露,攻击者可以:
- 访问数据库
- 伪造用户身份
- 使用付费 API(产生费用)

### Q: node_modules 为什么不应该提交?
**A**: 
- 文件数量巨大(数千到数万)
- 大小可能达到几百 MB
- 可以通过 `npm install` 重新生成
- 不同操作系统可能需要不同的编译版本

### Q: 如果我误删了重要文件怎么办?
**A**: 
```cmd
# 恢复已删除的文件
git restore <filename>

# 如果已经提交,从上一个提交恢复
git checkout HEAD~1 -- <filename>
```

## 快速参考命令

```cmd
# 查看被 Git 追踪的文件
git ls-files

# 查看特定文件是否被追踪
git ls-files | findstr "filename"

# 停止追踪文件(但保留本地)
git rm --cached <file>

# 停止追踪目录
git rm -r --cached <directory>

# 查看将要提交的内容
git status

# 撤销 git rm --cached
git restore --staged <file>

# 查看 .gitignore 是否生效
git check-ignore -v <file>
```

## 检查清单

- [ ] 备份项目
- [ ] 运行 `cleanup_git.bat`
- [ ] 检查 `git status` 输出
- [ ] 确认要删除的文件列表
- [ ] 提交更改
- [ ] 推送到远程
- [ ] 验证远程仓库
- [ ] 如果 .env 泄露,修改所有密码
- [ ] 通知团队成员
- [ ] 创建 .env.example 模板
- [ ] 更新 README 文档

---

**创建日期**: 2025年11月18日  
**版本**: v1.0  
**作者**: GitHub Copilot
