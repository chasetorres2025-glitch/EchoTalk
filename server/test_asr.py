#!/usr/bin/env python3
"""测试实时ASR"""
import dashscope
from dashscope.audio.asr import Recognition, RecognitionCallback
import time
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# 从环境变量获取API Key
dashscope.api_key = os.environ.get('ALIYUN_API_KEY')

if not dashscope.api_key:
    print("错误: 未设置 ALIYUN_API_KEY 环境变量")
    sys.exit(1)

result_text = []

class MyCallback(RecognitionCallback):
    def on_open(self):
        print('[Test] ASR 连接已打开', flush=True)
    
    def on_close(self):
        print('[Test] ASR 连接已关闭', flush=True)
    
    def on_event(self, result):
        print(f'[Test] 收到事件: {result}', flush=True)
        if result.get_sentence():
            text = result.get_sentence().get('text', '')
            print(f'[Test] 识别文本: {text}', flush=True)
            result_text.append(text)
    
    def on_error(self, error):
        print(f'[Test] 错误: {error}', flush=True)

print('[Test] 创建识别器...', flush=True)
recognition = Recognition(
    model='paraformer-realtime-v2',
    format='pcm',
    sample_rate=16000,
    language_hints=['zh', 'en'],
    callback=MyCallback()
)

print('[Test] 启动识别...', flush=True)
recognition.start()

# 发送一些静音数据
print('[Test] 发送静音数据...', flush=True)
silence = bytes(3200)  # 100ms of silence at 16kHz
for i in range(10):
    recognition.send_audio_frame(silence)
    time.sleep(0.1)

print('[Test] 等待结果...', flush=True)
time.sleep(2)

print('[Test] 停止识别...', flush=True)
result = recognition.stop()
print(f'[Test] 最终结果: {result}', flush=True)

print(f'[Test] 识别到的文本: {result_text}', flush=True)
