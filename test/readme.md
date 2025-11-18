# 测试文件说明

本目录包含 AI RAG Website 项目的各种测试脚本，用于验证后端 API、前端功能和系统集成。

## 📁 文件清单

### 1. `integration_test.py` - 集成测试脚本
**用途**: 测试 Django 后端与前端的整体集成功能

**功能**:
- ✅ 检查 Django 环境是否正常
- ✅ 验证数据库连接
- ✅ 测试 API 端点可用性
- ✅ 检查前端与后端的通信

**运行方式**:
```bash
cd test
python integration_test.py
```

**适用场景**:
- 部署后的系统验证
- CI/CD 流水线中的集成测试
- 整体功能健康检查

---

### 2. `test_ai_timeout.py` - AI 服务超时测试
**用途**: 测试 AI 服务的超时配置和处理机制

**功能**:
- ⏱️ 验证不同 AI 模型的超时配置
- ⏱️ 测试超时异常处理
- ⏱️ 检查各个模型（DeepSeek、GPT、Grok 等）的超时时间

**运行方式**:
```bash
cd test
python test_ai_timeout.py
```

**测试的模型**:
- DeepSeek 深度思考
- GPT-5
- Grok-4
- 通义千问
- 其他自定义模型

**适用场景**:
- AI 服务性能调优
- 超时配置验证
- 问题排查和调试

---

### 3. `test_category_api.py` - 分类 API 测试
**用途**: 测试文档分类相关的 API 接口

**功能**:
- 📂 测试分类的创建、读取、更新、删除（CRUD）
- 🔐 验证身份认证和授权
- ✅ 检查 API 响应格式和状态码

**API 端点**:
- `POST /api/token/` - 用户登录
- `GET /api/documents/categories/` - 获取分类列表
- `POST /api/documents/categories/` - 创建分类
- `PUT /api/documents/categories/{id}/` - 更新分类
- `DELETE /api/documents/categories/{id}/` - 删除分类

**运行前准备**:
1. 确保后端服务已启动（`http://localhost:8000`）
2. 修改脚本中的用户名和密码：
   ```python
   login_data = {
       "username": "admin",  # 修改为你的用户名
       "password": "admin123"  # 修改为你的密码
   }
   ```

**运行方式**:
```bash
cd test
python test_category_api.py
```

**适用场景**:
- 文档分类功能验证
- API 接口测试
- 回归测试

---

### 4. `test_documents_api.py` - 文档 API 测试
**用途**: 测试文档管理相关的 API 接口

**功能**:
- 📄 测试文档的上传、查询、更新、删除
- 🔍 验证文档搜索功能
- 📊 测试文档元数据管理

**API 端点**:
- `POST /api/token/` - 用户登录
- `GET /api/documents/` - 获取文档列表
- `POST /api/documents/` - 上传文档
- `GET /api/documents/{id}/` - 获取文档详情
- `PUT /api/documents/{id}/` - 更新文档
- `DELETE /api/documents/{id}/` - 删除文档

**运行前准备**:
1. 确保后端服务已启动
2. 配置正确的用户凭证
3. 准备测试用的文档文件

**运行方式**:
```bash
cd test
python test_documents_api.py
```

**适用场景**:
- 文档管理功能测试
- 文件上传/下载验证
- API 性能测试

---

### 5. `test_document_management.py` - 文档管理综合测试
**用途**: 综合测试分类、文件夹、文档的完整管理流程

**功能**:
- 🗂️ 测试分类创建和管理
- 📁 测试文件夹的层级结构
- 📄 测试文档的组织和归类
- 🔄 验证完整的工作流程

**测试流程**:
1. 用户登录认证
2. 创建文档分类
3. 创建文件夹结构
4. 上传文档到指定位置
5. 查询和过滤文档
6. 更新文档信息
7. 删除测试数据

**运行前准备**:
1. 确保后端服务运行在 `http://localhost:8000`
2. 修改登录凭证：
   ```python
   response = requests.post('http://localhost:8000/api/auth/login/', {
       'username': 'admin',  # 修改为你的用户名
       'password': 'admin123'  # 修改为你的密码
   })
   ```

**运行方式**:
```bash
cd test
python test_document_management.py
```

**适用场景**:
- 端到端功能测试
- 业务流程验证
- 用户场景模拟

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Django 后端服务已启动
- 必需的 Python 包：
  ```bash
  pip install requests django
  ```

### 通用运行步骤

1. **启动后端服务**
   ```bash
   cd backend
   python manage.py runserver
   ```

2. **创建测试用户**（如果没有）
   ```bash
   cd backend
   python manage.py createsuperuser
   ```

3. **修改测试脚本中的凭证**
   在各个测试文件中找到并修改：
   ```python
   login_data = {
       "username": "your_username",
       "password": "your_password"
   }
   ```

4. **运行测试**
   ```bash
   cd test
   python <测试文件名>.py
   ```

---

## 📊 测试结果示例

### 成功示例
```
=== 1. 登录 ===
✓ 登录成功，获取 token: eyJ0eXAiOiJKV1QiLCJ...

=== 2. 获取分类列表 ===
✓ 获取分类列表成功，共 3 个分类

=== 3. 创建分类 ===
✓ 创建分类成功: {'id': 4, 'name': '测试分类', ...}

=== 4. 更新分类 ===
✓ 更新分类成功

=== 5. 删除分类 ===
✓ 删除分类成功
```

### 失败示例
```
=== 1. 登录 ===
✗ 登录失败: 401 Client Error: Unauthorized

提示: 请检查用户名和密码是否正确
```

---

## 🔧 故障排查

### 常见问题

#### 1. 连接错误：`Connection refused`
**原因**: 后端服务未启动或端口不正确

**解决方案**:
```bash
# 检查服务是否运行
netstat -ano | findstr :8000

# 启动后端服务
cd backend
python manage.py runserver
```

#### 2. 认证失败：`401 Unauthorized`
**原因**: 用户名或密码错误

**解决方案**:
- 检查测试脚本中的凭证
- 确认用户已创建
- 使用 Django admin 重置密码

#### 3. 导入错误：`ModuleNotFoundError`
**原因**: 缺少必需的 Python 包

**解决方案**:
```bash
pip install -r requirements.txt
```

#### 4. 超时错误：`Timeout`
**原因**: AI 服务响应时间过长

**解决方案**:
- 检查网络连接
- 增加超时配置
- 使用 `test_ai_timeout.py` 调试

---

## 📝 编写新测试

### 测试模板

```python
"""
测试描述
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_your_feature():
    """测试功能说明"""
    
    # 1. 登录
    print("=== 1. 登录 ===")
    response = requests.post(f"{BASE_URL}/api/token/", {
        "username": "admin",
        "password": "admin123"
    })
    
    if response.status_code == 200:
        token = response.json()['access']
        headers = {'Authorization': f'Bearer {token}'}
        print("✓ 登录成功")
    else:
        print("✗ 登录失败")
        return
    
    # 2. 测试你的功能
    print("=== 2. 测试功能 ===")
    response = requests.get(
        f"{BASE_URL}/api/your-endpoint/",
        headers=headers
    )
    
    if response.status_code == 200:
        print("✓ 测试成功")
        print(f"返回数据: {response.json()}")
    else:
        print("✗ 测试失败")
        print(f"错误信息: {response.text}")

if __name__ == "__main__":
    test_your_feature()
```

---

## 🔒 安全注意事项

1. **不要提交包含真实密码的测试文件**
   - 使用环境变量存储敏感信息
   - 使用 `.env` 文件配置测试凭证

2. **测试数据清理**
   - 测试完成后删除创建的测试数据
   - 避免在生产环境运行测试

3. **Token 安全**
   - 不要在日志中打印完整的 token
   - 测试完成后清理 token

---

## 📚 相关文档

- [Django REST Framework 测试](https://www.django-rest-framework.org/api-guide/testing/)
- [Requests 库文档](https://requests.readthedocs.io/)
- [项目 API 文档](../docs/API.md)
- [后端开发文档](../backend/README.md)

---

## 🤝 贡献指南

添加新测试时请：

1. 遵循现有的命名规范（`test_*.py`）
2. 添加详细的文档字符串说明
3. 包含清晰的输出信息（使用 ✓ 和 ✗ 标记）
4. 更新本 README 文件
5. 确保测试可以独立运行

---

## 📅 更新日志

- **2025-11-18**: 创建测试目录 README
  - 添加所有现有测试文件的说明
  - 提供运行指南和故障排查
  - 添加测试模板和最佳实践

---

**维护者**: AI RAG Website 开发团队  
**最后更新**: 2025年11月18日
