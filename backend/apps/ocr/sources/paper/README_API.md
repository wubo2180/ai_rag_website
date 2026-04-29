# Dify 论文分析 REST API

这是一个基于 FastAPI 构建的 REST API 服务，用于通过网络接收 PDF 文件并调用 Dify 智能体 API 进行分析。

## 目录结构

```
.
├── config.yaml           # 配置文件
├── dify_client.py        # Dify API 客户端模块
├── api_server.py         # REST API 服务器
├── requirements.txt      # Python 依赖
├── test_4dataline.py     # 原始测试脚本（已保留）
└── README_API.md         # 本文档
```

## 安装

1. 安装依赖：

```bash
pip install -r requirements.txt
```

## 配置

编辑 `config.yaml` 文件来配置 Dify API 参数和服务器设置：

```yaml
# Dify API 配置
dify:
  base_url: "http://172.20.46.18:8088"      # Dify API 基础 URL
  api_key: "app-Xomtem4zJ9dkx23GcUbsUpNd"  # API 密钥
  default_user: "difyuser"                   # 默认用户标识
  
  # 文件上传配置
  upload:
    allowed_extensions:                      # 允许的文件类型
      - pdf
      - txt
      - doc
      - docx
    max_file_size: 50                        # 最大文件大小（MB）
  
  # 工作流配置
  workflow:
    response_mode: "blocking"                # 响应模式
    transfer_method: "local_file"
    file_type: "document"

# REST API 服务配置
api:
  host: "0.0.0.0"                            # 服务监听地址
  port: 8000                                 # 服务端口
  debug: true                                # 调试模式
  enable_cors: true                          # 启用 CORS
  temp_upload_dir: "./temp_uploads"          # 临时文件目录
```

## 启动服务

```bash
python api_server.py
```

服务将在 `http://0.0.0.0:8000` 启动。

## API 端点

### 1. 健康检查

**GET** `/health`

检查服务是否正常运行。

**响应示例：**
```json
{
  "status": "healthy",
  "dify_base_url": "http://172.20.46.18:8088"
}
```

### 2. 分析文件（一站式接口）

**POST** `/api/analyze`

上传文件并立即进行分析（推荐使用此接口）。

**请求参数：**
- `file` (multipart/form-data): PDF 文件
- `user` (form, 可选): 用户标识
- `response_mode` (form, 可选): 响应模式（blocking 或 streaming）

**请求示例（使用 curl）：**
```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -F "file=@/path/to/paper.pdf" \
  -F "user=myuser" \
  -F "response_mode=blocking"
```

**请求示例（使用 Python requests）：**
```python
import requests

url = "http://localhost:8000/api/analyze"
files = {'file': open('paper.pdf', 'rb')}
data = {'user': 'myuser', 'response_mode': 'blocking'}

response = requests.post(url, files=files, data=data)
print(response.json())
```

### 3. 上传文件

**POST** `/api/upload`

仅上传文件到 Dify，获取文件 ID。

**请求参数：**
- `file` (multipart/form-data): 要上传的文件
- `user` (form, 可选): 用户标识

**响应示例：**
```json
{
  "status": "success",
  "file_id": "abc123...",
  "filename": "paper.pdf"
}
```

### 4. 运行工作流

**POST** `/api/workflow/run`

使用已上传的文件 ID 运行 Dify 工作流。

**请求参数：**
- `file_id` (form): 文件 ID
- `user` (form, 可选): 用户标识
- `response_mode` (form, 可选): 响应模式

**请求示例：**
```bash
curl -X POST "http://localhost:8000/api/workflow/run" \
  -F "file_id=abc123..." \
  -F "user=myuser"
```

## API 文档

启动服务后，可以访问以下地址查看交互式 API 文档：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 使用 Dify 客户端模块

你也可以直接在 Python 代码中使用 `DifyClient` 类：

```python
from dify_client import DifyClient

# 初始化客户端
client = DifyClient(config_path="config.yaml")

# 方式 1：一站式处理文件
result = client.process_file(
    file_path="paper.pdf",
    user="myuser",
    response_mode="blocking"
)
print(result)

# 方式 2：分步骤处理
# 步骤 1: 上传文件
file_id = client.upload_file("paper.pdf", user="myuser")

# 步骤 2: 运行工作流
if file_id:
    result = client.run_workflow(file_id, user="myuser")
    print(result)
```

## 客户端示例

### JavaScript/Node.js

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

async function analyzePaper(filePath) {
  const form = new FormData();
  form.append('file', fs.createReadStream(filePath));
  form.append('user', 'myuser');
  form.append('response_mode', 'blocking');

  try {
    const response = await axios.post('http://localhost:8000/api/analyze', form, {
      headers: form.getHeaders()
    });
    console.log(response.data);
  } catch (error) {
    console.error('Error:', error.response.data);
  }
}

analyzePaper('./paper.pdf');
```

### Python

```python
import requests

def analyze_paper(file_path):
    url = "http://localhost:8000/api/analyze"
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'user': 'myuser',
            'response_mode': 'blocking'
        }
        
        response = requests.post(url, files=files, data=data)
        return response.json()

result = analyze_paper('./paper.pdf')
print(result)
```

## 错误处理

API 使用标准的 HTTP 状态码：

- `200`: 成功
- `400`: 请求错误（如不支持的文件类型、文件过大等）
- `500`: 服务器内部错误

错误响应格式：
```json
{
  "detail": "错误描述信息"
}
```

## 临时文件管理

- 上传的文件会临时保存在 `temp_uploads/` 目录中
- 文件处理完成后会自动删除临时文件
- 如果处理失败，临时文件也会被清理

## 安全建议

1. 在生产环境中，请修改 `config.yaml` 中的 `api_key`
2. 配置适当的 `allowed_origins` 来限制 CORS
3. 考虑添加身份验证机制
4. 使用 HTTPS 来保护数据传输
5. 设置合理的文件大小限制

## 疑难解答

### 服务无法启动
- 检查端口 8000 是否被占用
- 确认所有依赖已正确安装

### 文件上传失败
- 检查文件类型是否在允许的扩展名列表中
- 确认文件大小未超过限制
- 检查 Dify API 配置是否正确

### Dify API 连接失败
- 验证 `config.yaml` 中的 `base_url` 和 `api_key` 是否正确
- 确保网络连接正常
- 检查 Dify 服务是否正在运行

