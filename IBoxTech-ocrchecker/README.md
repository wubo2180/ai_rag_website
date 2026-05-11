# OCR 数据识别系统

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![Vue](https://img.shields.io/badge/vue-3.x-brightgreen.svg)
![Docker](https://img.shields.io/badge/docker-supported-blue.svg)

一个基于人工智能的检测报表识别系统，专为扫描PDF文档的自动化处理而设计。系统集成了先进的OCR技术，支持表格数据提取、手写内容识别和多用户协作工作流。

## ✨ 主要特性

- 🔍 **智能OCR识别** - 基于PaddleOCR的高精度文档识别
- 📊 **表格结构提取** - 自动识别和提取PDF中的表格数据
- ✍️ **手写内容识别** - 支持手写文字的识别和增强处理
- 👥 **多用户协作** - 完整的用户权限管理和工作流程
- 🖥️ **分屏核对界面** - 左侧数据编辑，右侧PDF预览的直观界面
- 📁 **文件批量处理** - 支持大批量文件的上传和处理
- 🔒 **企业级安全** - JWT认证，角色权限控制
- 🐳 **容器化部署** - 完整的Docker支持，一键部署

## 🛠️ 技术架构

### 后端技术栈
- **Web框架**: Flask 2.3.3
- **ORM**: SQLAlchemy 2.0.21
- **数据库**: MySQL 8.0+
- **OCR引擎**: PaddleOCR 2.7.0
- **对象存储**: MinIO
- **缓存**: Redis 6.0+
- **认证**: JWT (Flask-JWT-Extended)
- **图像处理**: OpenCV, Pillow
- **PDF处理**: PyMuPDF

### 前端技术栈
- **框架**: Vue.js 3.3.4
- **构建工具**: Vite 4.4.9
- **UI组件库**: Element Plus 2.3.9
- **状态管理**: Pinia 2.1.6
- **HTTP客户端**: Axios 1.5.0
- **PDF预览**: PDF.js 3.10.111
- **路由**: Vue Router 4.2.4

## 🚀 功能模块

### 1. 文件管理系统
- **批量上传**: 支持拖拽上传，同时处理多个PDF文件
- **文件预览**: 在线预览PDF文档，支持缩放、旋转
- **存储管理**: 基于MinIO的分布式对象存储
- **文件组织**: 支持标签分类、搜索过滤
- **访问控制**: 基于用户权限的文件访问管理

### 2. OCR识别引擎
- **高精度识别**: 基于PaddleOCR的中英文识别
- **表格提取**: 自动识别表格结构，提取行列数据
- **手写识别**: 专门的手写文字识别和增强算法
- **批量处理**: 支持大批量文件的异步处理
- **质量评估**: 识别结果置信度评分

### 3. 数据核对界面
- **分屏设计**: 左侧数据编辑，右侧PDF预览
- **实时同步**: 编辑操作与PDF区域高亮同步
- **版本控制**: 记录所有修改历史和操作日志
- **快捷操作**: 键盘快捷键支持，提升操作效率
- **数据验证**: 实时数据格式验证和错误提示

### 4. 用户权限系统
- **角色管理**: 管理员、普通用户角色区分
- **工作流程**: 文件分派、核对、审批流程
- **权限控制**: 细粒度的功能权限控制
- **操作审计**: 完整的用户操作日志记录

## 📁 项目结构

```
IBoxTech-data/
├── 📂 backend/                   # 后端服务
│   ├── 📂 app/
│   │   ├── 📂 api/              # REST API接口
│   │   ├── 📂 models/           # 数据库模型
│   │   ├── 📂 services/         # 业务逻辑服务
│   │   └── 📂 utils/            # 工具函数
│   ├── 📂 migrations/           # 数据库迁移
│   ├── 📂 config/               # 配置文件
│   ├── 📄 requirements.txt      # Python依赖
│   └── 📄 app.py               # 应用入口
├── 📂 frontend/                  # 前端应用
│   ├── 📂 src/
│   │   ├── 📂 components/       # Vue组件
│   │   ├── 📂 views/           # 页面视图
│   │   ├── 📂 stores/          # 状态管理
│   │   ├── 📂 api/             # API接口
│   │   └── 📂 utils/           # 工具函数
│   ├── 📄 package.json         # Node依赖
│   └── 📄 vite.config.js       # 构建配置
├── 📂 scripts/                   # 部署脚本
├── 📂 deployment/               # 部署配置
├── 📄 docker-compose.yml       # Docker编排
├── 📄 INSTALLATION.md          # 安装指南
├── 📄 DEPLOYMENT.md            # 部署指南
└── 📄 README.md                # 项目说明
```

## 🔧 快速开始

### 方式一：自动化安装（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/your-org/IBoxTech-data.git
cd IBoxTech-data

# 2. 运行自动化安装脚本
chmod +x scripts/setup.sh
./scripts/setup.sh

# 3. 启动服务
./scripts/start-backend.sh    # 启动后端 (端口5000)
./scripts/start-frontend.sh   # 启动前端 (端口5173)
```

### 方式二：Docker部署（生产环境）

```bash
# 1. 克隆项目
git clone https://github.com/your-org/IBoxTech-data.git
cd IBoxTech-data

# 2. 启动所有服务
docker-compose up -d

# 3. 查看服务状态
docker-compose ps
```

### 方式三：手动安装

详细的手动安装步骤请参考 [INSTALLATION.md](INSTALLATION.md)

## 🎯 系统使用

### 默认账户
安装完成后，系统会自动创建以下测试账户：

- **管理员账户**: `admin` / `admin123`
- **普通用户**: `testuser` / `test123`

### 访问地址
- **前端界面**: http://localhost:5173
- **后端API**: http://localhost:5000/api
- **健康检查**: http://localhost:5000/api/health
- **API文档**: http://localhost:5000/api/docs

### 基本操作流程

1. **登录系统** → 使用默认账户登录
2. **上传文件** → 批量上传PDF文件
3. **处理文件** → 系统自动进行OCR识别
4. **数据核对** → 在分屏界面核对和修正数据
5. **导出结果** → 导出处理后的结构化数据

## 🛡️ 系统要求

### 硬件要求
| 组件 | 最小配置 | 推荐配置 |
|------|----------|----------|
| CPU | 2核心 | 4核心+ |
| 内存 | 4GB | 8GB+ |
| 存储 | 20GB | 50GB+ |
| 网络 | 100Mbps | 1Gbps+ |

### 软件依赖
- **操作系统**: Linux (Ubuntu 20.04+) / macOS (10.15+) / Windows 10+
- **Python**: 3.8+ （推荐3.9+）
- **Node.js**: 16.0+ （推荐18.0+）
- **MySQL**: 8.0+
- **Redis**: 6.0+ （可选，用于缓存）
- **MinIO**: 最新版本
- **Docker**: 20.0+ （Docker部署时需要）

## 📊 性能指标

- **OCR处理速度**: 约2-5页/秒（取决于硬件配置）
- **文件上传大小**: 最大100MB/文件
- **并发用户数**: 支持100+并发用户
- **识别准确率**: 中文≥95%，英文≥98%
- **响应时间**: API响应时间<200ms

## 🤝 贡献指南

我们欢迎社区贡献！请参考以下步骤：

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📝 更新日志

### v1.0.0 (2024-01-15)
- ✨ 初始版本发布
- 🔍 集成PaddleOCR识别引擎
- 📊 实现表格数据提取
- 👥 完成多用户权限系统
- 🖥️ 开发分屏核对界面
- 🐳 支持Docker部署

## 🆘 故障排除

### 常见问题

**Q: 数据库连接失败**
A: 检查MySQL服务状态和配置文件中的连接参数

**Q: OCR识别速度慢**
A: 建议使用GPU加速，设置 `OCR_USE_GPU=true`

**Q: 文件上传失败**
A: 检查MinIO服务状态和存储空间

**Q: 前端无法访问后端API**
A: 检查CORS配置和防火墙设置

更多问题请查看 [Issues](https://github.com/your-org/IBoxTech-data/issues) 或参考详细的故障排除指南。

## 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源协议。

## 🙏 致谢

感谢以下开源项目的支持：
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - OCR识别引擎
- [Vue.js](https://vuejs.org/) - 前端框架
- [Flask](https://flask.palletsprojects.com/) - 后端框架
- [Element Plus](https://element-plus.org/) - UI组件库
- [MinIO](https://min.io/) - 对象存储

## 📞 联系我们

- 📧 Email: support@iboxtech.com
- 💬 QQ群: 123456789
- 🐛 Bug反馈: [GitHub Issues](https://github.com/your-org/IBoxTech-data/issues)
- 📖 文档站点: https://docs.iboxtech.com

---

⭐ 如果这个项目对您有帮助，请给我们一个Star！
