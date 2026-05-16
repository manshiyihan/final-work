#!/bin/bash

# Vue前端演示脚本

echo "======================================"
echo "  Vue前端演示向导"
echo "======================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查Node.js
echo -e "${BLUE}[1/5] 检查Node.js环境...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ 未检测到Node.js${NC}"
    echo "请访问 https://nodejs.org/ 安装Node.js"
    exit 1
fi
echo -e "${GREEN}✅ Node.js版本: $(node --version)${NC}"
echo ""

# 检查项目目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}❌ 未找到frontend目录${NC}"
    exit 1
fi

cd "$FRONTEND_DIR"

# 检查依赖
echo -e "${BLUE}[2/5] 检查项目依赖...${NC}"
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 首次运行，正在安装依赖...${NC}"
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 依赖安装失败${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ 依赖安装完成${NC}"
else
    echo -e "${GREEN}✅ 依赖已安装${NC}"
fi
echo ""

# 检查后端API
echo -e "${BLUE}[3/5] 检查后端API...${NC}"
API_URL="http://127.0.0.1:8000"
if curl -s "${API_URL}/api/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 后端API运行正常${NC}"
else
    echo -e "${YELLOW}⚠️  后端API未运行${NC}"
    echo ""
    echo "请在新终端窗口启动后端："
    echo -e "${BLUE}  cd $PROJECT_ROOT${NC}"
    echo -e "${BLUE}  ./scripts/run_api.sh${NC}"
    echo ""
    read -p "按Enter继续（后端启动后）..."
fi
echo ""

# 显示功能说明
echo -e "${BLUE}[4/5] 功能说明${NC}"
echo ""
echo "Vue前端提供以下功能："
echo ""
echo "1. 📁 本地文件检测"
echo "   - 拖拽上传音频文件"
echo "   - 支持wav/mp3/flac等格式"
echo "   - 实时预览和检测"
echo ""
echo "2. 🎤 录音检测"
echo "   - 浏览器内录音"
echo "   - 实时状态显示"
echo "   - 一键检测"
echo ""
echo "3. 👤 注册说话人"
echo "   - 录音注册"
echo "   - 文件上传注册"
echo "   - 自动格式转换"
echo ""
echo "4. 📊 历史记录"
echo "   - 分页查询"
echo "   - 多条件筛选"
echo "   - CSV导出"
echo ""

# 启动前端
echo -e "${BLUE}[5/5] 启动Vue前端...${NC}"
echo ""
echo -e "${GREEN}🚀 前端服务即将启动${NC}"
echo ""
echo "访问地址: ${BLUE}http://localhost:7860${NC}"
echo ""
echo "提示："
echo "  - 首次加载可能需要几秒钟"
echo "  - 录音功能需要允许麦克风权限"
echo "  - 按 Ctrl+C 停止服务"
echo ""
echo "======================================"
echo ""

sleep 2

npm run dev
