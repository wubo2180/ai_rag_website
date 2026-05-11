# OCR统一识别服务 - 快速开始

## 🚀 5分钟快速上手

### 1. 配置环境变量

编辑 `backend/.env` 文件，确保包含以下配置：

```bash
# 委托单OCR服务
OCR_COMMISSION_SERVICE_URL=http://localhost:6001

# 论文OCR服务  
OCR_PAPER_SERVICE_URL=http://localhost:6002

# 超时和重试配置
OCR_COMMISSION_TIMEOUT=300
OCR_PAPER_TIMEOUT=300
OCR_MAX_RETRIES=3
OCR_RETRY_DELAY=5
```

### 2. 启动所有服务

```bash
cd /home/h3c/workspace/IBoxTech-ocrchecker
./start_all_ocr_services.sh
```

### 3. 验证服务状态

```bash
# 检查所有服务
curl http://localhost:6001/health  # 委托单OCR
curl http://localhost:6002/health  # 论文OCR
curl http://localhost:5001/health  # 主系统
```

### 4. 使用OCR识别

前端调用（现有代码无需修改）：

```javascript
// 触发识别（自动根据文件类型路由）
const response = await recognizeApi.recognize(fileId)

// 获取任务状态
const status = await recognizeApi.getTaskStatus(taskId)
```

### 5. 停止所有服务

```bash
cd /home/h3c/workspace/IBoxTech-ocrchecker
./stop_all_ocr_services.sh
```

## 📋 服务端口

| 服务 | 端口 | 用途 |
|------|------|------|
| IBoxTech-ocrchecker | 5001 | 主系统API |
| IBoxTech-ocr-commission | 6001 | 委托单OCR识别 |
| IBoxTech-ocr-paper | 6002 | 论文OCR识别 |

## 📝 查看日志

```bash
# 实时查看委托单OCR日志
tail -f /tmp/ocr_commission.log

# 实时查看论文OCR日志
tail -f /tmp/ocr_paper.log

# 实时查看主系统日志
tail -f /tmp/ocrchecker.log
```

## 🔍 故障排查

### 问题1: 服务启动失败

```bash
# 检查端口是否被占用
lsof -i:6001
lsof -i:6002

# 手动停止并重启
./stop_all_ocr_services.sh
./start_all_ocr_services.sh
```

### 问题2: OCR识别失败

```bash
# 检查服务健康状态
curl http://localhost:6001/health
curl http://localhost:6002/health

# 查看错误日志
tail -100 /tmp/ocr_commission.log
tail -100 /tmp/ocr_paper.log
```

## 📚 详细文档

完整的技术文档请参阅: `docs/UNIFIED_OCR_INTEGRATION.md`

## ✅ 完成！

现在你的系统已经配置好统一的OCR识别服务，可以自动识别委托单和论文两种类型的文档了！


