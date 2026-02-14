#!/bin/bash

# EchoTalk 服务端部署脚本
# 适用于 CentOS 7.9
# 执行前请确保已上传代码到 /app/services/EchoTalk

set -e

echo "=========================================="
echo "EchoTalk 服务端部署脚本"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 部署目录
DEPLOY_DIR="/app/services/EchoTalk"

# 检查是否以 root 运行
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}请使用 root 用户运行此脚本${NC}"
    exit 1
fi

# 检查部署目录是否存在
if [ ! -d "$DEPLOY_DIR" ]; then
    echo -e "${RED}部署目录 $DEPLOY_DIR 不存在${NC}"
    echo "请先上传代码到该目录"
    exit 1
fi

cd "$DEPLOY_DIR"

echo ""
echo "=========================================="
echo "步骤 1/8: 检查系统环境"
echo "=========================================="

# 检查 Python 3.9
if ! command -v python3.9 &> /dev/null; then
    echo -e "${RED}Python 3.9 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3.9 已安装${NC}"

# 检查 MySQL
if ! command -v mysql &> /dev/null; then
    echo -e "${YELLOW}⚠ MySQL 客户端未安装${NC}"
else
    echo -e "${GREEN}✓ MySQL 已安装${NC}"
fi

# 检查 MongoDB
if ! command -v mongo &> /dev/null; then
    echo -e "${YELLOW}⚠ MongoDB 客户端未安装${NC}"
else
    echo -e "${GREEN}✓ MongoDB 已安装${NC}"
fi

# 检查 Nginx
if ! command -v nginx &> /dev/null; then
    echo -e "${YELLOW}⚠ Nginx 未安装${NC}"
else
    echo -e "${GREEN}✓ Nginx 已安装${NC}"
fi

echo ""
echo "=========================================="
echo "步骤 2/8: 创建 Python 虚拟环境"
echo "=========================================="

if [ ! -d "venv" ]; then
    python3.9 -m venv venv
    echo -e "${GREEN}✓ 虚拟环境创建成功${NC}"
else
    echo -e "${YELLOW}虚拟环境已存在，跳过创建${NC}"
fi

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
pip install --upgrade pip -q
echo -e "${GREEN}✓ pip 升级成功${NC}"

echo ""
echo "=========================================="
echo "步骤 3/8: 安装 Python 依赖"
echo "=========================================="

pip install -r requirements.txt -q
echo -e "${GREEN}✓ 依赖安装成功${NC}"

# 安装 gunicorn（如未安装）
if ! pip show gunicorn &> /dev/null; then
    pip install gunicorn -q
    echo -e "${GREEN}✓ Gunicorn 安装成功${NC}"
fi

echo ""
echo "=========================================="
echo "步骤 4/8: 创建必要的目录"
echo "=========================================="

mkdir -p logs uploads static
echo -e "${GREEN}✓ 目录创建成功${NC}"

echo ""
echo "=========================================="
echo "步骤 5/8: 配置环境变量"
echo "=========================================="

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ .env 文件不存在，正在创建模板...${NC}"
    cat > .env << 'EOF'
# Flask 安全配置
SECRET_KEY=change-this-secret-key-in-production

# MySQL 数据库配置
MYSQL_PASSWORD=your-mysql-password

# MongoDB 配置（如启用了认证）
MONGO_USER=
MONGO_PASSWORD=

# 微信小程序配置
WECHAT_APPID=your-wechat-appid
WECHAT_SECRET=your-wechat-secret

# 阿里云百炼平台 API Key
ALIYUN_API_KEY=your-aliyun-api-key

# 对象存储配置（可选）
OSS_ACCESS_KEY_ID=
OSS_ACCESS_KEY_SECRET=
COS_SECRET_ID=
COS_SECRET_KEY=
EOF
    chmod 600 .env
    echo -e "${YELLOW}⚠ 请编辑 .env 文件，填入真实的配置值${NC}"
else
    echo -e "${GREEN}✓ .env 文件已存在${NC}"
fi

echo ""
echo "=========================================="
echo "步骤 6/8: 配置 Systemd 服务"
echo "=========================================="

if [ -f "deploy/echotalk.service" ]; then
    cp deploy/echotalk.service /etc/systemd/system/
    systemctl daemon-reload
    echo -e "${GREEN}✓ Systemd 服务配置成功${NC}"
else
    echo -e "${RED}✗ 服务文件不存在${NC}"
fi

echo ""
echo "=========================================="
echo "步骤 7/8: 配置 Nginx"
echo "=========================================="

if [ -f "deploy/nginx-echotalk.conf" ]; then
    cp deploy/nginx-echotalk.conf /etc/nginx/conf.d/echotalk.conf
    nginx -t
    echo -e "${GREEN}✓ Nginx 配置成功${NC}"
else
    echo -e "${RED}✗ Nginx 配置文件不存在${NC}"
fi

echo ""
echo "=========================================="
echo "步骤 8/8: 初始化数据库"
echo "=========================================="

echo -e "${YELLOW}⚠ 即将初始化数据库，请确保 MySQL 和 MongoDB 已启动${NC}"
read -p "是否继续? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python init_db.py
    echo -e "${GREEN}✓ 数据库初始化完成${NC}"
else
    echo -e "${YELLOW}跳过数据库初始化${NC}"
fi

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "后续操作:"
echo "1. 编辑 .env 文件，填入真实的配置值:"
echo "   vim $DEPLOY_DIR/.env"
echo ""
echo "2. 启动服务:"
echo "   systemctl start echotalk"
echo ""
echo "3. 查看服务状态:"
echo "   systemctl status echotalk"
echo ""
echo "4. 查看日志:"
echo "   journalctl -u echotalk -f"
echo ""
echo "5. 测试接口:"
echo "   curl http://localhost:5050/health"
echo ""
echo "6. 配置防火墙:"
echo "   firewall-cmd --permanent --add-service=http"
echo "   firewall-cmd --reload"
echo ""
echo "=========================================="
