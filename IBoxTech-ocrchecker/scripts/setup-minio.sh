#!/bin/bash

# MinIO Docker 安装和配置脚本

echo "=== MinIO Docker 安装脚本 ==="

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装Docker"
    exit 1
fi

# 检查Docker Compose是否安装
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装Docker Compose"
    exit 1
fi

echo "✅ Docker 和 Docker Compose 已安装"

# 停止已存在的MinIO容器
echo "🔄 停止已存在的MinIO容器..."
docker compose -f docker-compose.minio.yml down 2>/dev/null || true

# 启动MinIO服务
echo "🚀 启动MinIO服务..."
docker compose -f docker-compose.minio.yml up -d

# 等待服务启动
echo "⏳ 等待MinIO服务启动..."
sleep 10

# 检查服务状态
if docker compose -f docker-compose.minio.yml ps | grep -q "running"; then
    echo "✅ MinIO服务启动成功！"
    echo ""
    echo "📊 访问信息："
    echo "   MinIO Console: http://localhost:9001"
    echo "   MinIO API:     http://localhost:9000"
    echo "   用户名:        minioadmin"
    echo "   密码:          minioadmin123"
    echo ""
    echo "🔧 常用命令："
    echo "   查看日志: docker compose -f docker-compose.minio.yml logs -f"
    echo "   停止服务: docker compose -f docker-compose.minio.yml down"
    echo "   重启服务: docker compose -f docker-compose.minio.yml restart"
else
    echo "❌ MinIO服务启动失败"
    echo "查看日志："
    docker compose -f docker-compose.minio.yml logs
    exit 1
fi
