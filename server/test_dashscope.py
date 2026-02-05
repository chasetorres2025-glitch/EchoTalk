#!/usr/bin/env python3
"""
测试 dashscope 导入和基本功能
"""
import sys

print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print()

# 测试导入
try:
    import dashscope
    print("✅ dashscope 导入成功")
    print(f"   dashscope 路径: {dashscope.__file__}")
    print(f"   dashscope 版本: {getattr(dashscope, '__version__', 'unknown')}")
    print()
    
    # 测试导入 Transcription
    try:
        from dashscope.audio.asr import Transcription
        print("✅ Transcription 导入成功")
    except Exception as e:
        print(f"❌ Transcription 导入失败: {e}")
    
    # 测试导入 File
    try:
        from dashscope import File
        print("✅ File 导入成功")
    except Exception as e:
        print(f"❌ File 导入失败: {e}")
    
    # 测试导入 SpeechSynthesizer
    try:
        from dashscope.audio.tts_v2 import SpeechSynthesizer
        print("✅ SpeechSynthesizer 导入成功")
    except Exception as e:
        print(f"❌ SpeechSynthesizer 导入失败: {e}")
        
except ImportError as e:
    print(f"❌ dashscope 导入失败: {e}")
    print("请运行: pip install dashscope")
