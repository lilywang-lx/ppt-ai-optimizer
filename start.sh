#!/bin/bash

echo "========================================="
echo "  PPT智能优化系统 - 快速启动脚本"
echo "========================================="
echo ""

# 检查是否安装Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未检测到Python3，请先安装Python 3.9+"
    exit 1
fi

# 检查是否安装Node.js
if ! command -v node &> /dev/null; then
    echo "⚠️  未检测到Node.js，将只启动后端服务"
    FRONTEND=false
else
    FRONTEND=true
fi

echo "📦 正在安装后端依赖..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo ""
echo "⚙️  请配置API Key..."
echo "请编辑 config/config.yaml 文件，填写各模型的API Key"
echo "按Enter键继续..."
read

echo ""
echo "🚀 启动后端服务..."
python main.py &
BACKEND_PID=$!
echo "后端服务已启动 (PID: $BACKEND_PID)"

if [ "$FRONTEND" = true ]; then
    echo ""
    echo "📦 正在安装前端依赖..."
    cd ../frontend
    npm install

    echo ""
    echo "🚀 启动前端服务..."
    npm run dev &
    FRONTEND_PID=$!
    echo "前端服务已启动 (PID: $FRONTEND_PID)"

    echo ""
    echo "========================================="
    echo "✅ 启动成功！"
    echo "========================================="
    echo "后端地址: http://localhost:8000"
    echo "后端文档: http://localhost:8000/docs"
    echo "前端地址: http://localhost:5173"
    echo ""
    echo "按Ctrl+C停止所有服务"
    echo "========================================="

    wait $BACKEND_PID $FRONTEND_PID
else
    echo ""
    echo "========================================="
    echo "✅ 后端启动成功！"
    echo "========================================="
    echo "后端地址: http://localhost:8000"
    echo "API文档: http://localhost:8000/docs"
    echo ""
    echo "按Ctrl+C停止服务"
    echo "========================================="

    wait $BACKEND_PID
fi
