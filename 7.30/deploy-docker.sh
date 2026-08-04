#!/bin/bash
# 保险精准营销系统 - Docker 一键部署脚本（macOS/Linux）
# 请确保已安装 Docker

set -e

echo "========================================"
echo "保险精准营销 AI 系统 - Docker 部署"
echo "========================================"
echo ""

# 检查 Docker 是否可用
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装或未启动！"
    echo ""
    echo "请先安装 Docker:"
    echo "  macOS: https://docs.docker.com/desktop/mac/install/"
    echo "  Linux: https://docs.docker.com/engine/install/"
    echo ""
    exit 1
fi

echo "✅ Docker 已就绪"
docker --version
echo ""

# 准备环境文件
if [ ! -f ".env" ]; then
    echo "📄 正在创建 .env 文件..."
    cp .env.docker .env
    echo "⚠️  请记得编辑 .env 中的 JWT_SECRET_KEY 和密码！"
fi

echo "📦 正在构建并启动容器..."
echo ""

docker-compose up -d --build

echo ""
echo "========================================"
echo "✅ 部署成功！"
echo "========================================"
echo ""
echo "访问地址: http://127.0.0.1:5000"
echo ""
echo "账号: admin"
echo "密码: admin123"
echo ""
echo "查看日志: docker-compose logs -f"
echo "停止服务: docker-compose down"
echo ""
