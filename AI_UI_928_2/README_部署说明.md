# Vue + Flask 聊天应用部署说明

## 项目结构
```
AI_UI_928_2/
├── backend/          # Flask后端
│   ├── app.py       # Flask应用主文件
│   └── requirements.txt
├── frontend/         # Vue前端
│   ├── src/         # Vue源码
│   ├── package.json
│   └── vite.config.js
└── start_app.ps1    # 一键启动脚本
```

## 环境要求
- Python 3.8+ 
- Node.js 16+
- npm 或 yarn

## 快速部署

### 方法一：使用一键启动脚本（推荐）
```powershell
# 在项目根目录执行
.\start_app.ps1
```

### 方法二：手动启动

#### 1. 启动后端（Flask）
```powershell
# 进入后端目录
cd backend

# 安装Python依赖
pip install -r requirements.txt

# 启动Flask服务器
python app.py
```
后端将运行在: http://localhost:5000

#### 2. 启动前端（Vue）
```powershell
# 新开一个终端，进入前端目录
cd frontend

# 安装Node.js依赖（如果还没安装）
npm install

# 启动Vue开发服务器
npm run dev
```
前端将运行在: http://localhost:5173

## 访问应用
- 前端界面: http://localhost:5173
- 后端API: http://localhost:5000

## API接口
- `POST /api/chat` - 聊天接口
- `POST /api/related-questions` - 相关问题推荐

## 功能特性
- 实时聊天对话
- 流式响应
- 多模型支持（deepseek、豆包、GPT-5）
- 深度思考模式
- 相关问题推荐
- 跨域支持

## 故障排除

### 常见问题
1. **端口被占用**
   - Flask默认端口：5000
   - Vue默认端口：5173
   - 如果端口被占用，请关闭占用进程或修改配置

2. **Python依赖问题**
   ```powershell
   pip install Flask Flask-Cors requests
   ```

3. **Node.js依赖问题**
   ```powershell
   cd frontend
   npm install
   ```

4. **跨域问题**
   - 后端已配置CORS，支持跨域请求

### 检查服务状态
```powershell
# 检查端口占用
netstat -ano | findstr :5000
netstat -ano | findstr :5173

# 检查进程
Get-Process | Where-Object {$_.ProcessName -eq "python"}
Get-Process | Where-Object {$_.ProcessName -eq "node"}
```

## 开发说明
- 前端使用Vue 3 + Vite
- 后端使用Flask + Flask-CORS
- 支持热重载开发
- 生产环境需要额外配置

## 注意事项
- 这是开发环境配置，生产环境需要额外的安全配置
- 确保防火墙允许相应端口访问
- 建议在虚拟环境中运行Python应用