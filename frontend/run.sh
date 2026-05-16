#!/bin/bash

# Vue前端启动脚本

cd "$(dirname "$0")"

echo "======================================"
echo "  抗欺诈说话人识别系统 - Vue前端"
echo "======================================"
echo ""

# 检查node是否安装
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未检测到 Node.js"
    echo "请先安装 Node.js (>= 14.18): https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js 版本: $(node --version)"
echo "✅ npm 版本: $(npm --version)"
echo ""

# 检查依赖是否安装
if [ ! -d "node_modules" ]; then
    echo "📦 首次运行，正在安装依赖..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
    echo "✅ 依赖安装完成"
    echo ""
fi

# 检查后端API
echo "🔍 检查后端API连接..."
API_URL="${COMB_API_BASE_URL:-http://127.0.0.1:8000}"
if curl -s "${API_URL}/api/health" > /dev/null 2>&1; then
    echo "✅ 后端API连接正常: ${API_URL}"
else
    echo "⚠️  警告: 无法连接到后端API: ${API_URL}"
    echo "   请确保后端服务已启动"
    echo "   启动命令: ./scripts/run_api.sh"
fi
echo ""

echo "🚀 启动Vue开发服务器..."
echo "   访问地址: http://localhost:7860"
echo "   按 Ctrl+C 停止服务"
echo ""

npm run dev
