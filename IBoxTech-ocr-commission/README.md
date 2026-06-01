# V3 OCR处理框架

V3是一个模块化的OCR文档处理框架，专注于业务逻辑与可视化分离、配置驱动的设计理念。

## 🏗️ 框架架构

```
V3/
├── config/           # 配置管理
├── core/            # 核心管道
├── steps/           # 处理步骤
├── utils/           # 工具类
├── visualization/   # 可视化
└── examples/        # 示例代码
```

## 🚀 快速开始

### 基础使用

```python
from pathlib import Path
from V3.config.settings import V3Config, DebugLevel
from V3.utils.logger import V3Logger
from V3.utils.file_manager import V3FileManager
from V3.steps.step1_preprocessing import PreprocessingStep

# 配置
config = V3Config(
    debug_level=DebugLevel.INFO,
    output_dir=Path("output")
)

# 初始化
logger = V3Logger(config)
file_manager = V3FileManager(config)

# 执行预处理
preprocessing_step = PreprocessingStep(config, file_manager, logger)
result_path = preprocessing_step.run("input.pdf")
```

### 启用分层倾斜校正

```python
# 配置分层校正
config.step_configs[1] = {
    'processing_params': {
        'use_layered_deskewing': True,
        'layered_method': 'stepwise'  # 推荐使用
    }
}
```

## 🔧 核心模块

### 配置管理 (`config/`)
- **`settings.py`**: 统一配置系统，支持调试级别、输出级别、步骤特定参数

### 核心框架 (`core/`)
- **`pipeline.py`**: 主管道编排器

### 处理步骤 (`steps/`)
- **`step1_preprocessing.py`**: 图像预处理
  - PDF转图像
  - 灰度化、去噪、增强、锐化
  - **高级分层倾斜校正** (新特性)
    - 结构层检测（长直线）
    - 文档层检测（边缘点群）
    - 内容层检测（投影分析）
    - 三种校正策略：分步/加权/最佳

### 工具类 (`utils/`)
- **`logger.py`**: 结构化日志系统
- **`file_manager.py`**: 统一文件管理
- **`base_step.py`**: 步骤基类

### 可视化 (`visualization/`)
- **`base_visualizer.py`**: 可视化基类
- **`step_visualizers.py`**: 步骤特定可视化

## 🎯 核心特性

### 1. 分层倾斜校正
V3框架的突出特性，提供比传统霍夫变换更精准的倾斜校正：

- **分步校正** (推荐): 先结构层后内容层
- **加权平均**: 多层角度智能组合  
- **最佳单一角度**: 投影方差最优选择

详细说明见：[LAYERED_DESKEWING_GUIDE.md](LAYERED_DESKEWING_GUIDE.md)

### 2. 业务逻辑与可视化分离
- 步骤类专注核心处理逻辑
- 可视化器独立处理展示需求
- 支持生产环境禁用可视化

### 3. 配置驱动架构
- 统一的配置管理系统
- 支持预设配置模板
- 步骤级参数定制

### 4. 结构化日志
- 多级别日志控制
- 性能指标追踪
- 调试信息详细记录

## 📊 性能对比

| 方法 | 检测精度 | 适用场景 | 处理速度 |
|------|----------|----------|----------|
| **V3分层校正** | ⭐⭐⭐⭐⭐ | 通用文档 | ⭐⭐⭐⭐ |
| 传统霍夫变换 | ⭐⭐⭐ | 简单倾斜 | ⭐⭐⭐⭐⭐ |

## 🛠️ 开发指南

### 添加新步骤

1. 继承`V3BaseStep`
2. 实现`execute`方法
3. 添加对应的可视化器
4. 更新配置模板

### 配置调优

```python
# 性能优化
config.step_configs[1] = {
    'processing_params': {
        'projection_angle_range': 2.0,    # 减小搜索范围
        'projection_angle_step': 0.5,     # 增大步长
    }
}

# 精度优化
config.step_configs[1] = {
    'processing_params': {
        'projection_angle_range': 5.0,    # 扩大搜索范围
        'projection_angle_step': 0.1,     # 减小步长
    }
}
```

## 📁 输出结构

```
output/
├── steps/           # 各步骤中间结果
├── visualizations/  # 可视化图像
├── debug/          # 调试数据
├── results/        # 最终结果
└── pipeline.log    # 执行日志
```

## 🔍 调试模式

```python
from V3.config.settings import DebugLevel

config = V3Config(debug_level=DebugLevel.DEBUG)
```

调试模式将输出：
- 详细的处理过程信息
- 角度检测和选择策略
- 中间结果的可视化
- 性能统计数据

## 📚 文档索引

- **[分层倾斜校正指南](LAYERED_DESKEWING_GUIDE.md)** - 详细使用说明
- **[示例代码](examples/)** - 完整测试用例

## 🎉 版本特性

### V3.0 (当前版本)
- ✅ 模块化架构设计
- ✅ 业务逻辑与可视化分离
- ✅ 高级分层倾斜校正
- ✅ 配置驱动的参数管理
- ✅ 结构化日志系统
- ✅ 完整的测试和文档

### 未来规划
- 🔄 更多预处理步骤
- 🔄 文本识别集成
- 🔄 表格检测与提取
- 🔄 字段智能提取

## 🤝 贡献

欢迎提交Issue和Pull Request来改进V3框架！

---

**V3 OCR框架 - 专业、高效、易用的文档处理解决方案**

