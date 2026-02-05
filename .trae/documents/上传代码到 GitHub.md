## 上传计划

由于项目尚未初始化 Git 仓库，需要使用完整的初始化流程：

### 执行步骤：

1. **创建 README.md**（如果不存在）
   ```bash
   echo "# EchoTalk" >> README.md
   ```

2. **初始化 Git 仓库**
   ```bash
   git init
   ```

3. **添加所有文件到暂存区**
   ```bash
   git add .
   ```

4. **提交初始版本**
   ```bash
   git commit -m "first commit"
   ```

5. **重命名主分支为 main**
   ```bash
   git branch -M main
   ```

6. **添加远程仓库**
   ```bash
   git remote add origin https://github.com/chasetorres2025-glitch/EchoTalk.git
   ```

7. **推送到 GitHub**
   ```bash
   git push -u origin main
   ```

### 注意事项：
- 项目已存在 `.gitignore` 文件，会自动忽略不需要上传的文件（如 `__pycache__`、`.env` 等）
- 推送前请确保你有 GitHub 仓库的写入权限
- 如果 GitHub 仓库已存在内容，可能需要先处理冲突