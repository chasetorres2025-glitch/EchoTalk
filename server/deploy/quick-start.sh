#!/bin/bash

# EchoTalk 快速启动脚本
# 用于日常启停服务

set -e

DEPLOY_DIR="/app/services/EchoTalk"
SERVICE_NAME="echotalk"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

show_help() {
    echo "EchoTalk 服务管理脚本"
    echo ""
    echo "用法: $0 {start|stop|restart|status|logs|health|backup|update}"
    echo ""
    echo "命令:"
    echo "  start    启动服务"
    echo "  stop     停止服务"
    echo "  restart  重启服务"
    echo "  status   查看服务状态"
    echo "  logs     查看实时日志"
    echo "  health   检查服务健康状态"
    echo "  backup   备份当前部署"
    echo "  update   更新部署（需要上传新代码）"
    echo ""
}

start_service() {
    echo -e "${BLUE}启动 EchoTalk 服务...${NC}"
    systemctl start $SERVICE_NAME
    sleep 2
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo -e "${GREEN}✓ 服务启动成功${NC}"
        check_health
    else
        echo -e "${RED}✗ 服务启动失败${NC}"
        systemctl status $SERVICE_NAME
    fi
}

stop_service() {
    echo -e "${BLUE}停止 EchoTalk 服务...${NC}"
    systemctl stop $SERVICE_NAME
    echo -e "${GREEN}✓ 服务已停止${NC}"
}

restart_service() {
    echo -e "${BLUE}重启 EchoTalk 服务...${NC}"
    systemctl restart $SERVICE_NAME
    sleep 2
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo -e "${GREEN}✓ 服务重启成功${NC}"
        check_health
    else
        echo -e "${RED}✗ 服务重启失败${NC}"
    fi
}

show_status() {
    echo -e "${BLUE}服务状态:${NC}"
    systemctl status $SERVICE_NAME --no-pager
}

show_logs() {
    echo -e "${BLUE}查看实时日志 (按 Ctrl+C 退出)...${NC}"
    journalctl -u $SERVICE_NAME -f
}

check_health() {
    echo -e "${BLUE}检查服务健康状态...${NC}"
    
    # 检查后端服务
    if curl -s http://localhost:5050/health > /dev/null; then
        echo -e "${GREEN}✓ 后端服务正常${NC}"
        curl -s http://localhost:5050/health | python3 -m json.tool 2>/dev/null || true
    else
        echo -e "${RED}✗ 后端服务异常${NC}"
    fi
    
    echo ""
    
    # 检查数据库连接
    if curl -s http://localhost:5050/health/db > /dev/null; then
        echo -e "${GREEN}✓ 数据库连接正常${NC}"
        curl -s http://localhost:5050/health/db | python3 -m json.tool 2>/dev/null || true
    else
        echo -e "${RED}✗ 数据库连接异常${NC}"
    fi
}

backup_deploy() {
    BACKUP_DIR="/app/services/backups"
    BACKUP_NAME="EchoTalk.backup.$(date +%Y%m%d_%H%M%S)"
    
    echo -e "${BLUE}备份当前部署...${NC}"
    mkdir -p $BACKUP_DIR
    
    # 排除日志和虚拟环境
    tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" \
        --exclude='venv' \
        --exclude='logs/*.log' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        -C /app/services EchoTalk
    
    echo -e "${GREEN}✓ 备份完成: $BACKUP_DIR/$BACKUP_NAME.tar.gz${NC}"
    
    # 清理旧备份（保留最近 10 个）
    ls -t $BACKUP_DIR/EchoTalk.backup.*.tar.gz 2>/dev/null | tail -n +11 | xargs -r rm
}

update_deploy() {
    echo -e "${YELLOW}⚠ 更新部署将停止服务并替换代码${NC}"
    read -p "是否继续? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "取消更新"
        return
    fi
    
    # 备份
    backup_deploy
    
    # 停止服务
    stop_service
    
    echo -e "${YELLOW}请上传新代码到 $DEPLOY_DIR${NC}"
    read -p "上传完成后按回车继续..."
    
    # 更新依赖
    cd $DEPLOY_DIR
    source venv/bin/activate
    pip install -r requirements.txt -q
    
    # 启动服务
    start_service
    
    echo -e "${GREEN}✓ 更新完成${NC}"
}

# 主逻辑
case "${1:-}" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    health)
        check_health
        ;;
    backup)
        backup_deploy
        ;;
    update)
        update_deploy
        ;;
    *)
        show_help
        exit 1
        ;;
esac
