## 阿里云百炼平台 API 适配改造计划

### 1. 配置清理与更新
**文件**: `config.ini`, `config.py`, `.env`

- 删除所有腾讯云相关配置 (TENCENT_*)
- 更新阿里云 API URL 为百炼平台最新接口
- 添加语音识别、语音合成相关配置
- 更新模型列表，支持通义千问系列、DeepSeek 等

### 2. AI 服务重构
**文件**: `app/utils/ai_service.py`

- 移除腾讯云相关代码
- 更新阿里云 API 调用方式，使用 OpenAI 兼容格式
- 实现语音识别功能 (Paraformer/Fun-ASR)
- 实现语音合成功能 (CosyVoice/Qwen-TTS)
- 优化回忆录生成和追问生成功能

### 3. 新增阿里云百炼客户端
**文件**: `app/utils/bailian_client.py` (新建)

- 封装阿里云百炼平台的通用调用逻辑
- 支持对话、语音识别、语音合成统一接口
- 实现错误处理和重试机制

### 4. 环境变量更新
**文件**: `.env.example`

- 移除腾讯云密钥
- 添加语音识别/合成 API Key
- 添加可选的模型配置

### 5. 依赖更新
**文件**: `requirements.txt`

- 添加 `dashscope` SDK (阿里云官方 Python SDK)
- 更新其他相关依赖

### 改造后能力
1. **对话**: 支持通义千问全系列 + DeepSeek-R1
2. **语音识别**: 支持实时识别和文件识别
3. **语音合成**: 支持多种音色和情感
4. **回忆录生成**: 基于对话历史自动生成文章
5. **追问生成**: 智能引导老人回忆细节

### 配置示例
```ini
[ai]
provider = aliyun
api_url = https://dashscope.aliyuncs.com/compatible-mode/v1
model = qwen-turbo
asr_model = paraformer-realtime-v2
tts_model = cosyvoice-v1
tts_voice = longxiaochun
```

请确认此计划后，我将开始实施具体的代码改造。