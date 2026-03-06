#!/bin/bash
# 生产排程智能体启动脚本 (Linux/Mac)

echo "========================================"
echo "生产排程智能体"
echo "========================================"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python3，请先安装 Python 3.8 或更高版本"
    echo "Ubuntu/Debian: sudo apt-get install python3 python3-venv python3-pip"
    echo "Mac: brew install python3"
    exit 1
fi

echo "[信息] 检测到 Python 版本:"
python3 --version
echo ""

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "[信息] 虚拟环境不存在，正在创建..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[错误] 创建虚拟环境失败"
        exit 1
    fi
    echo "[成功] 虚拟环境创建完成"
    echo ""
fi

# 激活虚拟环境
echo "[信息] 激活虚拟环境..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "[错误] 激活虚拟环境失败"
    exit 1
fi

# 检查依赖是否安装
python -c "import streamlit" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[信息] 检测到缺少依赖包，正在安装..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[错误] 安装依赖包失败"
        exit 1
    fi
    echo "[成功] 依赖包安装完成"
    echo ""
fi

# 启动应用
echo "[信息] 启动 Web 应用..."
echo "[提示] 浏览器将自动打开 http://localhost:8501"
echo "[提示] 按 Ctrl+C 可停止应用"
echo ""
streamlit run ui/app.py
