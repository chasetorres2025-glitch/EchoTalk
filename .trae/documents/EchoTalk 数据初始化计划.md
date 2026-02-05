## 数据初始化执行步骤

### 第1步：验证数据库服务状态
- 检查 MySQL 服务是否运行（端口 3306）
- 检查 MongoDB 服务是否运行（端口 27017）

### 第2步：执行数据初始化脚本
- 运行 `python init_db.py`
- 验证 MySQL 数据库和表创建成功
- 验证 MongoDB 集合和索引创建成功

### 第3步：验证初始化结果
- 检查 MySQL 中 `echotalk` 数据库及4张表
- 检查 MongoDB 中 `chat_log` 集合及索引

### 第4步：启动后端服务验证
- 运行 `python run.py` 启动服务
- 访问健康检查接口确认数据库连接正常

---

**执行命令：**
```bash
cd /Users/torres/Documents/trae_projects/EchoTalk/server
python init_db.py
```

**预期结果：**
- MySQL数据库初始化成功！
- MongoDB初始化成功！
- 数据库初始化完成！