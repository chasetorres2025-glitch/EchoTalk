## 项目概述
基于产品需求说明书，开发"EchoTalk老年人AI回忆录"MVP版本，包含微信小程序客户端和Python服务端。

## 环境检查 ✅
- Python 3.12.10 已安装
- pip 25.1.1 已安装  
- Node.js v23.11.0 已安装
- npm 10.9.2 已安装

## 目录结构设计

### 客户端 (client/) - 微信小程序
```
client/
├── pages/
│   ├── index/          # 首页 - "开始讲故事"按钮
│   ├── chat/           # 聊天界面 - 语音交互、实时转写
│   ├── article/        # 文章生成 - 展示、朗读、修改、保存
│   └── my-articles/    # 我的文章列表
├── utils/
│   └── api.js          # API请求封装
├── app.js              # 小程序入口
├── app.json            # 全局页面配置
└── app.wxss            # 全局样式（老年人友好：大字体、高对比度）
```

### 服务端 (server/) - Python Flask
```
server/
├── app/
│   ├── __init__.py
│   ├── models/         # MySQL/MongoDB数据模型
│   ├── routes/         # API路由（登录、聊天、文章、管理）
│   ├── services/       # 业务逻辑（AI调用、语音处理）
│   └── utils/          # 工具函数
├── config.py           # 数据库、AI接口配置
├── requirements.txt    # Flask、pymysql、pymongo等依赖
└── run.py              # 服务启动入口
```

## 核心功能实现

### 第一优先级（MVP核心）
1. **登录模块**：微信授权获取OpenID
2. **聊天模块**：语音采集、实时转写、上下文记录
3. **文章模块**：AI生成回忆录、朗读、保存
4. **数据存储**：MySQL用户/会话/文章表 + MongoDB聊天记录

### 技术栈
- **客户端**：微信小程序原生开发（WXML/WXSS/JS）
- **服务端**：Python + Flask
- **数据库**：MySQL（结构化数据）+ MongoDB（聊天记录）
- **AI接口**：预留阿里云通义千问/腾讯云混元对接

## 下一步
请确认此计划后，我将开始创建完整的客户端和服务端代码文件。