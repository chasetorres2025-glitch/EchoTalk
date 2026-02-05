## EchoTalk 后台管理系统设计方案

### 技术选型
- **前端**: 纯 HTML + Bootstrap 5（简洁、响应式、无需构建工具）
- **后端**: Flask + Blueprint（与现有服务端统一技术栈）
- **认证**: 简单的 Session-based 登录（固定管理员账号）
- **数据**: 复用现有 MySQL + MongoDB

### 功能模块

#### 1. 登录模块
- 管理员登录页面
- 简单的 session 认证

#### 2. 数据概览 Dashboard
- 用户总数
- 今日新增用户
- 会话总数
- 文章总数
- 今日聊天记录数

#### 3. 用户管理
- 用户列表（分页展示）
- 查看用户详情
- 查看用户的所有会话
- 查看用户的所有文章

#### 4. 会话管理
- 会话列表（分页展示）
- 查看会话详情
- 查看会话的聊天记录
- 删除会话

#### 5. 文章管理
- 文章列表（分页展示）
- 查看文章详情
- 预览文章内容
- 删除文章

#### 6. 系统管理
- 系统配置查看
- 日志查看（可选）

### 文件结构
```
server/
├── app/
│   ├── routes/
│   │   └── admin.py          # 后台管理路由
│   └── templates/
│       └── admin/            # 后台页面模板
│           ├── base.html     # 基础模板
│           ├── login.html    # 登录页
│           ├── dashboard.html # 数据概览
│           ├── users.html    # 用户管理
│           ├── sessions.html # 会话管理
│           ├── articles.html # 文章管理
│           └── detail_*.html # 详情页
├── static/admin/             # 静态资源
│   ├── css/
│   └── js/
```

### 路由设计
- `GET /admin/login` - 登录页面
- `POST /admin/login` - 登录提交
- `GET /admin/logout` - 退出登录
- `GET /admin/` - 管理后台首页（Dashboard）
- `GET /admin/users` - 用户列表
- `GET /admin/users/<id>` - 用户详情
- `GET /admin/sessions` - 会话列表
- `GET /admin/sessions/<id>` - 会话详情
- `GET /admin/articles` - 文章列表
- `GET /admin/articles/<id>` - 文章详情

### 安全考虑
- 简单的登录认证
- 登录状态检查装饰器
- 密码使用环境变量配置

请确认此方案后，我将开始实现后台管理系统的代码。