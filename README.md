# EchoTalk

EchoTalk - 老年人AI回忆录产品

## 项目简介

EchoTalk 是一个专为老年人设计的AI回忆录产品，通过语音对话的方式帮助老年人记录和分享他们的人生故事。

## 项目结构

```
EchoTalk/
├── client/          # 微信小程序客户端
│   ├── pages/       # 页面文件
│   ├── utils/       # 工具函数
│   └── app.js       # 小程序入口
├── server/          # Python Flask 后端服务
│   ├── app/         # 应用代码
│   │   ├── routes/  # 路由模块
│   │   └── utils/   # 工具模块
│   ├── uploads/     # 上传文件目录
│   └── run.py       # 服务启动文件
└── .trae/           # 项目文档
```

## 技术栈

- **前端**: 微信小程序
- **后端**: Python Flask
- **数据库**: MongoDB
- **AI服务**: 阿里云百炼平台

## 功能模块

- 语音对话
- 文章管理
- 用户认证
- AI回忆录生成

## 启动服务

### 后端服务
```bash
cd server
pip install -r requirements.txt
python run.py
```

### 微信小程序
使用微信开发者工具打开 `client` 目录
