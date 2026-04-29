#!/bin/bash

# OCR数据识别系统安装脚本
# 支持 macOS 和 Linux

set -e

echo "🚀 开始安装OCR数据识别系统..."
echo "=================================="

# 检查操作系统
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    *)          MACHINE="UNKNOWN:${OS}"
esac
echo "检测到操作系统: ${MACHINE}"

# 检查Python版本
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        echo "✅ 检测到Python版本: ${PYTHON_VERSION}"
        
        # 检查版本是否 >= 3.8
        if python3 -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)"; then
            echo "✅ Python版本满足要求"
        else
            echo "❌ Python版本需要 >= 3.8"
            exit 1
        fi
    else
        echo "❌ 未检测到Python3，请先安装Python 3.8+"
        exit 1
    fi
}

# 检查Node.js版本
check_nodejs() {
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        echo "✅ 检测到Node.js版本: ${NODE_VERSION}"
        
        # 检查版本是否 >= 16
        NODE_MAJOR=$(echo $NODE_VERSION | cut -d'.' -f1 | cut -d'v' -f2)
        if [ "$NODE_MAJOR" -ge 16 ]; then
            echo "✅ Node.js版本满足要求"
        else
            echo "❌ Node.js版本需要 >= 16"
            exit 1
        fi
    else
        echo "❌ 未检测到Node.js，请先安装Node.js 16+"
        exit 1
    fi
}

# 检查MySQL
check_mysql() {
    if command -v mysql &> /dev/null; then
        MYSQL_VERSION=$(mysql --version)
        echo "✅ 检测到MySQL: ${MYSQL_VERSION}"
    else
        echo "⚠️  未检测到MySQL，请确保MySQL服务已安装并运行"
        echo "   安装方法:"
        if [ "$MACHINE" = "Mac" ]; then
            echo "   brew install mysql"
        else
            echo "   sudo apt-get install mysql-server  # Ubuntu/Debian"
            echo "   sudo yum install mysql-server      # CentOS/RHEL"
        fi
    fi
}

# 检查Redis
check_redis() {
    if command -v redis-server &> /dev/null; then
        echo "✅ 检测到Redis"
    else
        echo "⚠️  未检测到Redis，请确保Redis服务已安装并运行"
        echo "   安装方法:"
        if [ "$MACHINE" = "Mac" ]; then
            echo "   brew install redis"
        else
            echo "   sudo apt-get install redis-server  # Ubuntu/Debian"
            echo "   sudo yum install redis             # CentOS/RHEL"
        fi
    fi
}

# 安装后端依赖
install_backend_deps() {
    echo ""
    echo "📦 安装后端Python依赖..."
    cd backend
    
    # 创建虚拟环境（如果不存在）
    if [ ! -d "venv" ]; then
        echo "创建Python虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装依赖
    pip install -r requirements.txt
    
    echo "✅ 后端依赖安装完成"
    cd ..
}

# 安装前端依赖
install_frontend_deps() {
    echo ""
    echo "📦 安装前端Node.js依赖..."
    cd frontend
    
    # 安装依赖
    npm install
    
    echo "✅ 前端依赖安装完成"
    cd ..
}

# 创建配置文件
create_config_files() {
    echo ""
    echo "⚙️  创建配置文件..."
    
    # 创建后端环境配置文件
    if [ ! -f "backend/.env" ]; then
        cp backend/env_example.txt backend/.env
        echo "✅ 创建后端环境配置文件: backend/.env"
        echo "   请编辑此文件以配置数据库和其他服务"
    else
        echo "⚠️  后端环境配置文件已存在: backend/.env"
    fi
    
    # 创建前端环境配置文件
    if [ ! -f "frontend/.env" ]; then
        echo "VITE_API_BASE_URL=http://localhost:5000/api" > frontend/.env
        echo "✅ 创建前端环境配置文件: frontend/.env"
    else
        echo "⚠️  前端环境配置文件已存在: frontend/.env"
    fi
}

# 创建必要目录
create_directories() {
    echo ""
    echo "📁 创建必要目录..."
    
    mkdir -p backend/logs
    mkdir -p backend/models
    mkdir -p backend/uploads
    
    echo "✅ 目录创建完成"
}

# 初始化数据库
init_database() {
    echo ""
    echo "🗄️  初始化数据库..."
    echo "请确保MySQL服务已启动，并且已创建数据库 'ocr_system'"
    echo ""
    read -p "是否现在初始化数据库？(y/N): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd backend
        source venv/bin/activate
        python migrations/init_database.py
        cd ..
    else
        echo "⚠️  跳过数据库初始化，请稍后手动运行:"
        echo "   cd backend && source venv/bin/activate && python migrations/init_database.py"
    fi
}

# 主安装流程
main() {
    # 检查系统依赖
    check_python
    check_nodejs
    check_mysql
    check_redis
    
    # 安装项目依赖
    install_backend_deps
    install_frontend_deps
    
    # 创建配置文件
    create_config_files
    
    # 创建目录
    create_directories
    
    # 初始化数据库
    init_database
    
    echo ""
    echo "=================================="
    echo "🎉 安装完成!"
    echo ""
    echo "📋 下一步:"
    echo "1. 编辑配置文件:"
    echo "   • backend/.env  - 后端配置（数据库、Redis、MinIO等）"
    echo "   • frontend/.env - 前端配置"
    echo ""
    echo "2. 启动服务:"
    echo "   • 启动后端: ./scripts/start-backend.sh"
    echo "   • 启动前端: ./scripts/start-frontend.sh"
    echo "   • 或使用Docker: docker-compose up -d"
    echo ""
    echo "3. 访问系统:"
    echo "   • 前端地址: http://localhost:5173"
    echo "   • 后端API: http://localhost:5000/api"
    echo ""
    echo "4. 默认账户:"
    echo "   • 管理员: admin / admin123"
    echo "   • 测试用户: testuser / test123"
    echo ""
    echo "📚 更多信息请查看 README.md 和 DEPLOYMENT.md"
}

# 执行主函数
main
