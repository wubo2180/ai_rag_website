# 统一OCR识别服务集成文档

## 📖 概述

本文档描述了如何将两个独立的OCR识别服务（委托单OCR和论文OCR）统一集成到IBoxTech-ocrchecker系统中。通过统一的接口层，系统可以根据文档类型自动路由到相应的OCR服务。

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                      IBoxTech-ocrchecker                         │
│                    (主系统 - 端口: 5001)                          │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Unified OCR Service                         │  │
│  │           (统一OCR路由服务)                               │  │
│  │                                                           │  │
│  │  ┌──────────────┐        ┌──────────────┐              │  │
│  │  │ document_type│        │document_type │              │  │
│  │  │ = commission │        │  = paper     │              │  │
│  │  └───────┬──────┘        └───────┬──────┘              │  │
│  │          │                       │                      │  │
│  │          v                       v                      │  │
│  │  ┌──────────────┐        ┌──────────────┐              │  │
│  │  │ Commission   │        │  Paper OCR   │              │  │
│  │  │ OCR Handler  │        │   Handler    │              │  │
│  │  └───────┬──────┘        └───────┬──────┘              │  │
│  └──────────┼────────────────────────┼─────────────────────┘  │
│             │                        │                         │
└─────────────┼────────────────────────┼─────────────────────────┘
              │                        │
              │ HTTP POST              │ HTTP POST
              v                        v
┌─────────────────────────┐  ┌───────────────────────────┐
│  IBoxTech-ocr-commission│  │   IBoxTech-ocr-paper      │
│    (委托单OCR服务)       │  │     (论文OCR服务)          │
│    端口: 6001            │  │     端口: 6002             │
│    端点: /analyze        │  │     端点: /api/analyze     │
└─────────────────────────┘  └───────────────────────────┘
```

## 📁 文件结构

```
IBoxTech-ocrchecker/
├── backend/
│   ├── config/
│   │   └── config.py                    # ✅ 已更新：添加OCR服务配置
│   ├── app/
│   │   ├── api/
│   │   │   └── files.py                 # ✅ 使用现有OCR端点
│   │   └── services/
│   │       ├── unified_ocr_service.py   # ✨ 新增：统一OCR路由服务
│   │       └── ocr_task_service.py      # ✅ 已更新：使用统一服务
│   └── .env                              # 需要手动配置
└── docs/
    └── UNIFIED_OCR_INTEGRATION.md       # 📚 本文档
```

## 🔧 配置说明

### 1. 环境变量配置

在 `backend/.env` 文件中添加以下配置：

```bash
# ==================== 外部OCR服务配置 ====================

# 委托单OCR服务配置
OCR_COMMISSION_SERVICE_URL=http://localhost:6001
OCR_COMMISSION_TIMEOUT=300

# 论文OCR服务配置  
OCR_PAPER_SERVICE_URL=http://localhost:6002
OCR_PAPER_TIMEOUT=300

# OCR服务重试配置
OCR_MAX_RETRIES=3
OCR_RETRY_DELAY=5
```

### 2. OCR服务端口说明

| 服务 | 端口 | 分析端点 | 健康检查端点 |
|------|------|---------|-------------|
| IBoxTech-ocrchecker | 5001 | `/api/files/{file_id}/ocr/recognize` | `/health` |
| IBoxTech-ocr-commission | 6001 | `/analyze` | `/health` |
| IBoxTech-ocr-paper | 6002 | `/api/analyze` | `/health` |

## 🚀 启动服务

### 启动顺序

1. **启动委托单OCR服务** (端口: 6001)
   ```bash
   cd /home/h3c/workspace/IBoxTech-ocr-commission
   python api_server.py
   # 或使用后台启动脚本:
   ./run_api_background.sh
   ```

2. **启动论文OCR服务** (端口: 6002)
   ```bash
   cd /home/h3c/workspace/IBoxTech-ocr-paper
   python api_server.py
   # 或使用nohup后台启动:
   nohup python api_server.py > nohup.out 2>&1 &
   ```

3. **启动主系统** (端口: 5001)
   ```bash
   cd /home/h3c/workspace/IBoxTech-ocrchecker/backend
   python app.py
   ```

### 验证服务启动

```bash
# 检查委托单OCR服务
curl http://localhost:6001/health

# 检查论文OCR服务
curl http://localhost:6002/health

# 检查主系统
curl http://localhost:5001/health
```

## 📝 API使用说明

### 前端调用示例

```javascript
import { recognizeApi } from '@/api/recognize'

// 触发OCR识别（自动根据文件类型路由）
const response = await recognizeApi.recognize(fileId)

// 返回格式
{
  "success": true,
  "message": "OCR识别任务已创建",
  "data": {
    "task_id": "uuid-string",
    "file_id": 123,
    "status": "pending"
  }
}

// 轮询任务状态
const statusResponse = await recognizeApi.getTaskStatus(taskId)

// 任务完成后的结果格式
{
  "success": true,
  "data": {
    "task_id": "uuid-string",
    "status": "completed",
    "progress": 100,
    "result": {
      "structured_data": {...},      // 结构化数据
      "raw_ocr_data": {...},          // 原始OCR数据
      "document_type": "commission",  // 文档类型
      "confidence": 0.95              // 置信度
    }
  }
}
```

### 后端处理流程

1. **接收识别请求**
   - API端点: `POST /api/files/{file_id}/ocr/recognize`
   - 创建异步任务并立即返回任务ID

2. **后台处理**
   - 从MinIO下载文件
   - 获取文件的`document_type_code`
   - 调用`UnifiedOCRService.recognize_file()`

3. **统一OCR服务路由**
   - 根据`document_type_code`选择服务：
     - `commission` → 委托单OCR服务 (6001端口)
     - `paper` → 论文OCR服务 (6002端口)
   - 发送文件到对应服务
   - 处理响应并统一格式

4. **结果解析**
   - **委托单**: 解析为 `{basic_info, test_items, special_tests}` 格式
   - **论文**: 直接返回OCR服务的结果

5. **保存结果**
   - 更新任务状态为`completed`
   - 保存结构化数据和原始数据

## 🔄 数据流转

### 委托单识别流程

```
前端 → 主系统API → UnifiedOCRService 
  ↓                      ↓
  识别请求          document_type='commission'
  ↓                      ↓
返回task_id       → 委托单OCR服务(6001)
  ↓                      ↓
轮询状态          ← 返回field_extraction_results
  ↓                      ↓
获取结果          解析为basic_info/test_items/special_tests
  ↓                      ↓
显示数据          ← 保存到task.result
```

### 论文识别流程

```
前端 → 主系统API → UnifiedOCRService 
  ↓                      ↓
  识别请求          document_type='paper'
  ↓                      ↓
返回task_id       → 论文OCR服务(6002)
  ↓                      ↓
轮询状态          ← 返回论文分析结果
  ↓                      ↓
获取结果          直接使用返回数据
  ↓                      ↓
显示数据          ← 保存到task.result
```

## 🧪 测试方法

### 1. 单元测试：健康检查

```bash
cd /home/h3c/workspace/IBoxTech-ocrchecker/backend

python << 'EOF'
from app import create_app
from services.unified_ocr_service import unified_ocr_service

app = create_app()
with app.app_context():
    # 测试委托单服务健康
    healthy, data, error = unified_ocr_service.check_service_health('commission')
    print(f"委托单服务: {'✅ 健康' if healthy else '❌ 不健康'}")
    if not healthy:
        print(f"  错误: {error}")
    
    # 测试论文服务健康
    healthy, data, error = unified_ocr_service.check_service_health('paper')
    print(f"论文服务: {'✅ 健康' if healthy else '❌ 不健康'}")
    if not healthy:
        print(f"  错误: {error}")
EOF
```

### 2. 集成测试：完整流程

```bash
# 创建测试脚本
cat > /tmp/test_ocr_integration.py << 'EOF'
#!/usr/bin/env python3
"""
OCR统一接口集成测试
"""
import requests
import time
import json

BASE_URL = "http://localhost:5001/api"

def login():
    """登录获取token"""
    response = requests.post(
        f"{BASE_URL}/login",
        json={"username": "admin", "password": "admin123"}
    )
    return response.json()['data']['access_token']

def trigger_ocr(file_id, token):
    """触发OCR识别"""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.post(
        f"{BASE_URL}/files/{file_id}/ocr/recognize",
        headers=headers
    )
    return response.json()

def get_task_status(task_id, token):
    """获取任务状态"""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        f"{BASE_URL}/files/ocr/task/{task_id}",
        headers=headers
    )
    return response.json()

def main():
    print("🧪 开始OCR统一接口集成测试...\n")
    
    # 1. 登录
    print("1️⃣ 登录系统...")
    token = login()
    print(f"   ✅ 登录成功\n")
    
    # 2. 测试委托单识别
    print("2️⃣ 测试委托单识别...")
    file_id = input("   请输入委托单文件ID: ")
    result = trigger_ocr(file_id, token)
    
    if result['success']:
        task_id = result['data']['task_id']
        print(f"   ✅ 任务已创建: {task_id}")
        
        # 轮询任务状态
        print("   ⏳ 等待识别完成...")
        while True:
            status = get_task_status(task_id, token)
            if status['success']:
                task_status = status['data']['status']
                progress = status['data'].get('progress', 0)
                print(f"      状态: {task_status}, 进度: {progress}%")
                
                if task_status == 'completed':
                    print(f"   ✅ 识别完成！")
                    print(f"   结果:\n{json.dumps(status['data']['result'], indent=2, ensure_ascii=False)[:500]}...")
                    break
                elif task_status == 'failed':
                    print(f"   ❌ 识别失败: {status['data'].get('error_message')}")
                    break
            
            time.sleep(2)
    else:
        print(f"   ❌ 创建任务失败: {result['message']}")
    
    print("\n✅ 测试完成！")

if __name__ == '__main__':
    main()
EOF

python /tmp/test_ocr_integration.py
```

## 📊 监控和日志

### 查看OCR服务日志

```bash
# 委托单OCR服务日志
tail -f /home/h3c/workspace/IBoxTech-ocr-commission/logs/api_server_*.log

# 论文OCR服务日志
tail -f /home/h3c/workspace/IBoxTech-ocr-paper/nohup.out

# 主系统日志
tail -f /home/h3c/workspace/IBoxTech-ocrchecker/backend/app.log
```

### 关键日志标识

- `[UnifiedOCR]` - 统一OCR服务日志
- `[CommissionOCR]` - 委托单OCR调用日志
- `[PaperOCR]` - 论文OCR调用日志
- `[Task {task_id}]` - 任务处理日志

## ⚙️ 故障排查

### 1. OCR服务连接失败

**症状**: 
```
❌ [CommissionOCR] 连接失败: Connection refused
```

**解决方案**:
1. 检查OCR服务是否启动: `curl http://localhost:6001/health`
2. 检查端口是否正确: `netstat -tlnp | grep 6001`
3. 检查防火墙规则
4. 检查配置文件中的URL是否正确

### 2. OCR识别超时

**症状**:
```
⏱️ [CommissionOCR] 请求超时 (300秒)
```

**解决方案**:
1. 增加超时时间: 修改`.env`中的`OCR_COMMISSION_TIMEOUT`
2. 检查OCR服务性能
3. 检查网络延迟

### 3. 文档类型识别错误

**症状**:
```
❌ [UnifiedOCR] 不支持的文档类型: unknown
```

**解决方案**:
1. 确保文件上传时指定了`document_type_code`
2. 检查文件表中的`document_type_code`字段
3. 添加默认值逻辑

### 4. OCR结果格式不匹配

**症状**:
```
❌ 解析OCR结果失败: KeyError: 'extracted_fields'
```

**解决方案**:
1. 检查OCR服务返回的数据格式
2. 更新`_parse_ocr_api_result`方法以适配新格式
3. 添加格式验证和容错处理

## 🔒 安全考虑

1. **API认证**: 所有OCR服务应配置API密钥认证
2. **网络隔离**: OCR服务应在内网运行，不对外暴露
3. **速率限制**: 对OCR识别接口实施速率限制
4. **文件验证**: 上传文件前进行格式和大小验证
5. **日志脱敏**: 日志中不记录敏感数据

## 📈 性能优化

1. **并发处理**: 使用Celery替代线程池处理OCR任务
2. **结果缓存**: 对相同文件的识别结果进行缓存
3. **服务扩展**: 使用负载均衡器部署多个OCR服务实例
4. **资源监控**: 监控OCR服务的CPU、内存使用情况

## 🔄 版本升级

### v1.0 → v2.0 (添加新OCR服务)

1. 在`config.py`中添加新服务配置
2. 在`UnifiedOCRService`中添加服务映射
3. 实现对应的`_recognize_xxx`方法
4. 更新前端`document_type_code`选项
5. 添加健康检查和测试用例

## 📞 支持

如有问题，请联系：
- 技术支持: tech@iboxtech.com
- 文档维护: dev@iboxtech.com

---

**最后更新**: 2025-11-09
**版本**: v1.0
**作者**: IBoxTech开发团队


