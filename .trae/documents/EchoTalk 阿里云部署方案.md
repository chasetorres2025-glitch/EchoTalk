# EchoTalk 阿里云部署方案

## 项目概况
- **框架**: Flask 3.0.0
- **数据库**: MySQL + MongoDB
- **端口**: 5050
- **Python版本**: 需要 3.7+ (服务器已有3.6.8，需升级)

## 部署步骤

### 第一阶段：服务器环境准备

1. **升级 Python 到 3.9+**
   - CentOS 7 默认 Python 3.6.8 版本过低
   - 需要从源码编译安装 Python 3.9 或 3.10

2. **安装 MySQL 5.7+**
   - 使用 yum 安装 MySQL 社区版
   - 创建 echotalk 数据库和用户

3. **安装 MongoDB 4.0+**
   - 添加 MongoDB 官方 yum 源
   - 安装并启动 MongoDB 服务

4. **安装 Nginx**
   - 作为反向代理
   - 配置 SSL 证书（HTTPS）

### 第二阶段：项目部署

5. **上传项目代码**
   - 使用 git clone 或 scp 上传
   - 创建生产环境配置文件

6. **配置生产环境**
   - 修改 config.ini 为生产环境配置
   - 创建 .env 文件并配置敏感信息
   - 修改 MySQL/MongoDB 连接为本地连接

7. **安装 Python 依赖**
   - 创建虚拟环境
   - pip install -r requirements.txt

8. **初始化数据库**
   - 运行 python init_db.py 创建数据表

### 第三阶段：服务启动与守护

9. **使用 Gunicorn 启动服务**
   - 安装 gunicorn
   - 配置多工作进程

10. **配置 Systemd 服务**
    - 创建 echotalk.service
    - 设置开机自启

11. **配置 Nginx 反向代理**
    - 转发到 5050 端口
    - 配置静态文件服务

### 第四阶段：安全与优化

12. **配置防火墙**
    - 开放 80/443 端口
    - 关闭 5050 外部访问

13. **配置域名和 SSL**
    - 申请 SSL 证书
    - 配置 HTTPS 访问

## 执行命令概览

```bash
# 1. 安装 Python 3.9
sudo yum install -y gcc openssl-devel bzip2-devel libffi-devel zlib-devel wget
wget https://www.python.org/ftp/python/3.9.18/Python-3.9.18.tgz
tar xzf Python-3.9.18.tgz
cd Python-3.9.18
./configure --enable-optimizations
sudo make altinstall

# 2. 安装 MySQL
wget https://dev.mysql.com/get/mysql57-community-release-el7-11.noarch.rpm
sudo rpm -Uvh mysql57-community-release-el7-11.noarch.rpm
sudo yum install -y mysql-community-server
sudo systemctl start mysqld
sudo systemctl enable mysqld

# 3. 安装 MongoDB
cat > /etc/yum.repos.d/mongodb-org-4.4.repo << 'EOF'
[mongodb-org-4.4]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/4.4/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-4.4.asc
EOF
sudo yum install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod

# 4. 安装 Nginx
sudo yum install -y epel-release
sudo yum install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# 5. 部署项目
cd /opt
git clone <your-repo> echotalk
cd echotalk/server
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# 6. 配置并启动
# (编辑配置文件)
python init_db.py
gunicorn -w 4 -b 127.0.0.1:5050 "app:create_app()"
```

## 注意事项

1. **Python 版本**: 服务器自带的 3.6.8 不满足 Flask 3.0 要求，必须升级
2. **内存限制**: 1.7GB 内存较小，建议配置 swap 空间
3. **安全配置**: 生产环境必须修改所有默认密码和密钥
4. **数据库**: MySQL 和 MongoDB 都需要配置安全认证

请确认这个部署方案后，我将为你生成详细的部署脚本和配置文件。