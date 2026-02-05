## 任务计划

### 1. 环境现状
- ✅ MySQL 8.0.42 已安装
- ❌ MongoDB 未安装

### 2. 任务一：整合所有环境配置到配置文件
将分散的配置信息统一整合到 `server/config.py`，包括：
- Flask基础配置（SECRET_KEY, DEBUG）
- MySQL配置（主机、端口、用户名、密码、数据库名）
- MongoDB配置（URI、数据库名）
- 微信小程序配置（APPID, SECRET）
- AI大模型配置（阿里云/腾讯云 API Key、URL）
- 对象存储配置（OSS/COS AccessKey、Bucket等）
- 语音配置（最大录音时长、格式）

### 3. 任务二：本地安装MongoDB
通过Homebrew安装MongoDB社区版：
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

### 4. 验证步骤
- 检查MongoDB安装状态
- 验证MongoDB服务启动
- 测试数据库连接

请确认此计划后，我将开始执行具体的配置整合和MongoDB安装操作。