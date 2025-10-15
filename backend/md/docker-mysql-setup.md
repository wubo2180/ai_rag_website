# 🐳 MySQL Docker 配置指南

## 📋 Docker Desktop 界面配置

### 1. 基础设置
- **Image**: `mysql:8.0`
- **Container name**: `ai_rag_mysql`

### 2. 端口配置 (Ports)
```
Host port: 3306
Container port: 3306
```

### 3. 环境变量 (Environment variables)
| Variable | Value |
|----------|-------|
| `MYSQL_ROOT_PASSWORD` | `airag123456` |
| `MYSQL_DATABASE` | `ai_rag_db` |
| `MYSQL_USER` | `ai_rag_user` |
| `MYSQL_PASSWORD` | `airag_user123` |

### 4. 数据卷 (Volumes)
```
Host path: E:\document\python_workspace\mysql_data
Container path: /var/lib/mysql
```

## 🚀 命令行方式启动 (可选)

```bash
# 创建数据目录
mkdir E:\document\python_workspace\mysql_data

# 运行MySQL容器
docker run -d \
  --name ai_rag_mysql \
  -p 3306:3306 \
  -e MYSQL_ROOT_PASSWORD=airag123456 \
  -e MYSQL_DATABASE=ai_rag_db \
  -e MYSQL_USER=ai_rag_user \
  -e MYSQL_PASSWORD=airag_user123 \
  -v E:\document\python_workspace\mysql_data:/var/lib/mysql \
  mysql:8.0
```

## 🔧 Django 数据库配置

更新您的 `settings.py`：

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'ai_rag_db',
        'USER': 'ai_rag_user',
        'PASSWORD': 'airag_user123',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}
```

## 📦 Python依赖

需要安装MySQL客户端：
```bash
pip install mysqlclient
# 或者
pip install PyMySQL
```

如果使用PyMySQL，需在Django项目的 `__init__.py` 中添加：
```python
import pymysql
pymysql.install_as_MySQLdb()
```

## 🔍 验证连接

```bash
# 进入容器
docker exec -it ai_rag_mysql mysql -u ai_rag_user -p

# 查看数据库
SHOW DATABASES;
USE ai_rag_db;
SHOW TABLES;
```

## 🛠️ 常用管理命令

```bash
# 查看容器状态
docker ps

# 停止容器
docker stop ai_rag_mysql

# 启动容器
docker start ai_rag_mysql

# 查看日志
docker logs ai_rag_mysql

# 备份数据库
docker exec ai_rag_mysql mysqldump -u ai_rag_user -p ai_rag_db > backup.sql
```

## ⚠️ 注意事项

1. **密码安全**: 生产环境请使用强密码
2. **数据持久化**: 确保设置了volume映射
3. **防火墙**: 确保3306端口可访问
4. **字符集**: 建议使用utf8mb4支持完整Unicode