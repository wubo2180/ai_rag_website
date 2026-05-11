# 🔧 依赖版本兼容性指南

## PaddlePaddle 3.2.0 版本适配

根据您的要求，现已将系统调整为使用 PaddlePaddle 3.2.0 版本。

## 📋 当前版本配置

### 核心OCR依赖
- **PaddlePaddle**: 3.2.0 (用户指定版本)
- **PaddleOCR**: 2.7.3 (最新稳定版，兼容 PaddlePaddle 3.x)
- **OpenCV**: >=4.8.0,<5.0.0 (与新版本兼容)
- **Pillow**: >=10.0.0,<11.0.0 (图像处理)

### 数据库依赖
- **SQLAlchemy**: >=2.0.16,<2.1.0 (Flask-SQLAlchemy 3.1.1兼容)
- **Flask-SQLAlchemy**: 3.1.1
- **PyMySQL**: 1.1.0

## 🚀 推荐安装步骤

### 方式1：清洁安装
```bash
# 1. 删除现有虚拟环境
rm -rf venv

# 2. 创建新虚拟环境
python3 -m venv venv
source venv/bin/activate

# 3. 升级pip
python -m pip install --upgrade pip

# 4. 安装依赖
pip install -r backend/requirements.txt
```

### 方式2：分步安装（推荐）
```bash
# 1. 激活虚拟环境
source venv/bin/activate

# 2. 升级pip
python -m pip install --upgrade pip

# 3. 先安装PaddlePaddle框架
pip install paddlepaddle==3.2.0

# 4. 安装PaddleOCR
pip install paddleocr==2.7.3

# 5. 安装其他依赖
pip install -r backend/requirements.txt
```

### 方式3：GPU版本（如有NVIDIA GPU）
```bash
# 安装GPU版本的PaddlePaddle
pip install paddlepaddle-gpu==3.2.0
pip install paddleocr==2.7.3
pip install -r backend/requirements.txt
```

## ⚠️ 已知兼容性问题及解决方案

### 1. 网络下载问题
PaddlePaddle 3.2.0 文件较大(~100MB)，如遇下载超时：
```bash
# 设置更长超时时间
pip install --timeout=600 paddlepaddle==3.2.0

# 或使用国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple paddlepaddle==3.2.0
```

### 2. macOS Apple Silicon兼容性
如使用 Apple M1/M2 芯片：
```bash
# 确保安装ARM64版本
pip install paddlepaddle==3.2.0 --force-reinstall
```

### 3. 依赖冲突处理
如遇到其他包冲突：
```bash
# 使用pip-tools解决冲突
pip install pip-tools
pip-compile backend/requirements.in
```

## 🧪 验证安装

安装完成后，运行以下代码验证：

```python
import paddleocr
import paddlepaddle
import cv2

print(f"PaddlePaddle版本: {paddlepaddle.__version__}")
print(f"PaddleOCR版本: {paddleocr.__version__}")
print(f"OpenCV版本: {cv2.__version__}")

# 测试OCR功能
ocr = paddleocr.PaddleOCR(use_angle_cls=True, lang='ch')
print("✅ PaddleOCR初始化成功")
```

## 🔄 版本升级历史

| 日期 | PaddlePaddle | PaddleOCR | 说明 |
|------|-------------|-----------|------|
| 2024-09-18 | 2.5.2 | 2.7.0.3 | 初始版本 |
| 2024-09-18 | 3.2.0 | 2.7.3 | 用户要求升级 |

## 💡 性能优化建议

### GPU加速配置
```bash
# 在.env文件中设置
OCR_USE_GPU=true
PADDLE_USE_GPU=true
```

### 内存优化
```bash
# 限制内存使用
export CUDA_VISIBLE_DEVICES=0
export FLAGS_fraction_of_gpu_memory_to_use=0.5
```

## 🆘 故障排除

### 常见错误及解决方案

**错误1**: `ImportError: No module named 'paddle'`
```bash
# 解决方案
pip uninstall paddlepaddle paddleocr
pip install paddlepaddle==3.2.0
pip install paddleocr==2.7.3
```

**错误2**: `OpenCV version conflict`
```bash
# 解决方案
pip uninstall opencv-python opencv-python-headless
pip install opencv-python>=4.8.0,<5.0.0
```

**错误3**: `CUDA version mismatch`
```bash
# 检查CUDA版本
nvidia-smi

# 安装对应版本的PaddlePaddle
pip install paddlepaddle-gpu==3.2.0 -f https://www.paddlepaddle.org.cn/packages/stable/cu118.html
```

## 📞 技术支持

如遇到问题，请参考：
1. PaddlePaddle官方文档: https://www.paddlepaddle.org.cn/
2. PaddleOCR项目页面: https://github.com/PaddlePaddle/PaddleOCR
3. 项目Issue反馈: [GitHub Issues]

---
**更新日期**: 2024年9月18日  
**适用版本**: PaddlePaddle 3.2.0 + PaddleOCR 2.7.3
