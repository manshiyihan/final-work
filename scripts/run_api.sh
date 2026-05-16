#!/bin/bash

echo "正在启动 Conformer 反欺诈后端 API..."

if ! python -c "import fastapi" 2>/dev/null; then
    echo "正在安装 API 依赖..."
    pip install -r requirements_api.txt
fi

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
