# EchoTalk 服务端部署指南

## 服务器环境信息

- **操作系统**: CentOS 7.9
- **内存**: 1.7GB
- **部署路径**: `/app/services/EchoTalk`
- **Python**: 3.9 (已安装)
- **MongoDB**: 4.4.30 (已安装)
- **MySQL**: 8.0.44 (已安装)
- **Nginx**: 1.20.1 (已安装)

---

## 一、部署前准备

### 1.1 本地准备

在本地项目根目录执行以下命令，准备部署包：

```bash
# 进入服务端目录
cd /Users/torres/Documents/trae_projects/EchoTalk/server

# 创建部署包（排除开发文件）
tar -czvf echotalk-server.tar.gz \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.git' \
  --exclude='.env' \
  --exclude='venv' \
  --exclude='.pytest_cache' \
  --exclude='logs/*.log' \
  --exclude='uploads/*' \
  .
```

### 1.2 上传到服务器

使用 SFTP 上传部署包到服务器：

```bash
# 使用 scp 上传（在本地执行）
scp echotalk-server.tar.gz root@你的服务器IP:/app/services/

# 或者使用 rsync 上传整个目录
rsync -avz --exclude='__pycache__' --exclude='*.pyc' --exclude='.git' --exclude='venv' \
  /Users/torres/Documents/trae_projects/EchoTalk/server/ \
  root@你的服务器IP:/app/services/EchoTalk/
```

---

## 二、服务器端部署步骤

### 2.1 解压部署包（如使用 tar.gz）

```bash
# 创建部署目录
mkdir -p /app/services/EchoTalk
cd /app/services

# 解压
tar -xzvf echotalk-server.tar.gz -C EchoTalk/

# 设置权限
chown -R root:root /app/services/EchoTalk
```

### 2.2 创建 Python 虚拟环境

```bash
cd /app/services/EchoTalk

# 创建虚拟环境
python3.9 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt
```

### 2.3 配置环境变量

```bash
cd /app/services/EchoTalk

# 创建 .env 文件
cat > .env << 'EOF'
# Flask 安全配置
SECRET_KEY=your-secret-key-here-change-in-production

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

# 设置权限（仅 root 可读）
chmod 600 .env
```

### 2.4 修改配置文件

编辑 `config.ini`，根据实际环境调整：

```bash
cd /app/services/EchoTalk

# 修改数据库配置（如需要）
# 生产环境建议关闭 debug
sed -i 's/debug = true/debug = false/' config.ini

# 确认端口配置
sed -i 's/port = 5050/port = 5050/' config.ini
```

### 2.5 初始化数据库

```bash
cd /app/services/EchoTalk

# 激活虚拟环境
source venv/bin/activate

# 初始化数据库
python init_db.py
```

### 2.6 创建必要的目录

```bash
cd /app/services/EchoTalk

# 创建日志目录
mkdir -p logs

# 创建上传文件目录
mkdir -p uploads

# 创建静态文件目录
mkdir -p static

# 设置权限
chmod 755 logs uploads static
```

---

## 三、配置 Systemd 服务

### 3.1 复制服务文件

```bash
# 复制 systemd 服务文件
cp /app/services/EchoTalk/deploy/echotalk.service /etc/systemd/system/

# 重新加载 systemd
systemctl daemon-reload

# 设置开机自启
systemctl enable echotalk
```

### 3.2 管理服务

```bash
# 启动服务
systemctl start echotalk

# 停止服务
systemctl stop echotalk

# 重启服务
systemctl restart echotalk

# 查看状态
systemctl status echotalk

# 查看日志
journalctl -u echotalk -f
```

---

## 四、配置 Nginx 反向代理

### 4.1 选择部署方式

根据你的服务器环境，选择以下三种方式之一：

#### 方式一：添加到现有配置（推荐，与现有服务共存）

如果服务器上已有其他服务在运行（如 even_sys_app），需要修改 `/etc/nginx/nginx.conf`：

```bash
# 1. 备份原配置
cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup.$(date +%Y%m%d)

# 2. 编辑 nginx.conf，添加以下内容：
# 在 http 块中，existing upstream 旁边添加：
upstream echotalk_backend {
    server 127.0.0.1:5050;
    keepalive 32;
}

# 3. 在现有的 server 块中，添加 location 配置（参考 deploy/nginx-echotalk.conf 中的方式一）

# 4. 测试并重载
nginx -t
systemctl reload nginx
```

**或者直接使用以下命令追加配置：**

```bash
# 添加 upstream
cat >> /etc/nginx/nginx.conf << 'EOF'

upstream echotalk_backend {
    server 127.0.0.1:5050;
    keepalive 32;
}
EOF

# 然后手动编辑 server 块添加 location
vim /etc/nginx/nginx.conf
```

访问地址：
- 管理后台：`http://你的服务器IP/echotalk/admin/`
- API 接口：`http://你的服务器IP/echotalk/api/`
- 健康检查：`http://你的服务器IP/echotalk/health`

#### 方式二：独立端口（无需修改主配置）

使用 8080 端口访问，将配置放到 conf.d 目录：

```bash
# 复制配置文件
cp /app/services/EchoTalk/deploy/nginx-echotalk.conf /etc/nginx/conf.d/echotalk.conf

# 编辑配置文件，注释掉方式一，取消注释方式二
vim /etc/nginx/conf.d/echotalk.conf

# 测试并重载
nginx -t
systemctl reload nginx
```

访问地址：
- 管理后台：`http://你的服务器IP:8080/admin/`

#### 方式三：独立域名（需要 DNS 配置）

如果你有独立域名（如 `echotalk.your-domain.com`）：

```bash
# 复制配置文件
cp /app/services/EchoTalk/deploy/nginx-echotalk.conf /etc/nginx/conf.d/echotalk.conf

# 编辑配置文件，取消注释方式三，设置 server_name
vim /etc/nginx/conf.d/echotalk.conf
# 修改 server_name echotalk.your-domain.com;

# 测试并重载
nginx -t
systemctl reload nginx
```

### 4.2 防火墙配置

```bash
# 开放 HTTP/HTTPS 端口
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https

# 如使用独立端口（方式二），开放对应端口
firewall-cmd --permanent --add-port=8080/tcp

# 如需要直接访问后端端口（测试用）
firewall-cmd --permanent --add-port=5050/tcp

# 重载防火墙
firewall-cmd --reload
```

---

## 五、验证部署

### 5.1 检查服务状态

```bash
# 检查后端服务
curl http://localhost:5050/health

# 检查数据库连接
curl http://localhost:5050/health/db

# 检查 Nginx 代理（根据部署方式选择）
# 方式一（路径前缀）
curl http://localhost/echotalk/health

# 方式二（独立端口）
curl http://localhost:8080/health

# 方式三（独立域名）
curl http://echotalk.your-domain.com/health
```

### 5.2 预期响应

健康检查接口应返回：

```json
{
  "code": 0,
  "message": "OK",
  "env": false
}
```

数据库健康检查应返回：

```json
{
  "code": 0,
  "message": "Database connections OK",
  "mysql": "connected",
  "mongodb": "connected"
}
```

---

## 六、日志查看

### 6.1 应用日志

```bash
# 查看应用日志
tail -f /app/services/EchoTalk/logs/echotalk.log

# 查看 systemd 日志
journalctl -u echotalk -f
```

### 6.2 Nginx 日志

```bash
# 访问日志
tail -f /var/log/nginx/access.log

# 错误日志
tail -f /var/log/nginx/error.log
```

---

## 七、常见问题排查

### 7.1 服务无法启动

```bash
# 检查 Python 环境
source /app/services/EchoTalk/venv/bin/activate
python --version

# 检查依赖
pip list

# 手动运行测试
cd /app/services/EchoTalk
python run.py
```

### 7.2 数据库连接失败

```bash
# 检查 MySQL
mysql -u root -p -e "SHOW DATABASES;"

# 检查 MongoDB
mongo --eval "db.adminCommand('ping')"
```

### 7.3 端口被占用

```bash
# 检查端口占用
netstat -tlnp | grep 5050

# 或
ss -tlnp | grep 5050
```

---

## 八、更新部署

### 8.1 更新代码

```bash
# 进入部署目录
cd /app/services/EchoTalk

# 备份当前版本
cp -r /app/services/EchoTalk /app/services/EchoTalk.backup.$(date +%Y%m%d)

# 停止服务
systemctl stop echotalk

# 上传新代码（通过 SFTP）

# 安装新依赖
source venv/bin/activate
pip install -r requirements.txt

# 重启服务
systemctl start echotalk
```

### 8.2 数据库迁移

如需数据库结构变更：

```bash
cd /app/services/EchoTalk
source venv/bin/activate
python init_db.py
```

---

## 九、安全建议

1. **修改默认密码**: 确保 MySQL、MongoDB 使用强密码
2. **配置防火墙**: 仅开放必要的端口
3. **使用 HTTPS**: 生产环境建议配置 SSL 证书
4. **定期备份**: 设置数据库自动备份
5. **日志审计**: 定期检查日志文件

---

## 十、性能优化（1.7GB 内存）

由于服务器内存较小，建议：

1. **调整 MySQL 配置**:
   ```ini
   # /etc/my.cnf.d/mysql-server.cnf
   [mysqld]
   innodb_buffer_pool_size = 256M
   key_buffer_size = 16M
   query_cache_size = 16M
   max_connections = 50
   ```

2. **调整 MongoDB 配置**:
   ```yaml
   # /etc/mongod.conf
   storage:
     wiredTiger:
       engineConfig:
         cacheSizeGB: 0.25
   ```

3. **使用 Gunicorn 替代 Flask 开发服务器**（已在服务文件中配置）

4. **启用 Swap**（如未启用）：
   ```bash
   # 创建 2GB swap
   dd if=/dev/zero of=/swapfile bs=1M count=2048
   mkswap /swapfile
   swapon /swapfile
   echo '/swapfile none swap sw 0 0' >> /etc/fstab
   ```
