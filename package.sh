#!/bin/bash

echo "========================================"
echo "生产排程系统打包脚本"
echo "========================================"
echo ""

echo "[1/4] 清理旧文件..."
rm -rf dist
rm -f *.tar.gz

echo "[2/4] 创建发布目录..."
mkdir -p dist/production-scheduler

echo "[3/4] 复制项目文件..."
cp -r data_layer dist/production-scheduler/
cp -r business_logic dist/production-scheduler/
cp -r ui dist/production-scheduler/
cp -r docs dist/production-scheduler/
cp requirements.txt dist/production-scheduler/
cp README.md dist/production-scheduler/
cp DEPLOYMENT.md dist/production-scheduler/
cp run.sh dist/production-scheduler/
cp Dockerfile dist/production-scheduler/
cp docker-compose.yml dist/production-scheduler/

# 设置执行权限
chmod +x dist/production-scheduler/run.sh

echo "[4/4] 创建压缩包..."
cd dist
tar -czf ../production-scheduler-v1.0.0.tar.gz production-scheduler
cd ..

echo ""
echo "========================================"
echo "打包完成！"
echo "输出文件: production-scheduler-v1.0.0.tar.gz"
echo "========================================"
