"""
AI服务统一接口
基于阿里云百炼平台实现对话、语音识别、语音合成、回忆录生成等功能
"""
from typing import Optional, List, Dict, Union
from .bailian_client import bailian_client


class AIService:
    """AI服务统一接口类"""
    
    def __init__(self):
        # 使用百炼客户端
        self.client = bailian_client
    
    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> Optional[str]:
        """
        调用AI大模型进行对话
        
        Args:
            messages: 消息列表 [{"role": "system/user/assistant", "content": "..."}]
            temperature: 温度参数
            
        Returns:
            AI回复文本
        """
        try:
            return self.client.chat_completion(
                messages=messages,
                temperature=temperature
            )
        except Exception as e:
            print(f"AI对话调用失败: {e}")
            return None
    
    def speech_to_text(self, audio_file_path: str) -> Optional[str]:
        """
        语音识别 - 将音频转换为文字
        
        Args:
            audio_file_path: 音频文件路径
            
        Returns:
            识别出的文本
        """
        try:
            return self.client.speech_to_text(audio_file_path)
        except Exception as e:
            print(f"语音识别失败: {e}")
            return None
    
    def text_to_speech(self, 
                      text: str, 
                      output_path: Optional[str] = None,
                      use_sdk: bool = True) -> Optional[Union[str, bytes]]:
        """
        语音合成 - 将文字转换为音频
        
        Args:
            text: 要合成的文本
            output_path: 输出文件路径，为None则返回音频数据
            use_sdk: 是否使用 dashscope SDK (推荐)
            
        Returns:
            有output_path时返回文件路径，否则返回音频字节数据
        """
        try:
            if use_sdk:
                # 优先使用 SDK 方式
                return self.client.text_to_speech_with_dashscope(text, output_path=output_path)
            else:
                # 使用 HTTP API 方式
                return self.client.text_to_speech(text, output_path=output_path)
        except Exception as e:
            print(f"语音合成失败: {e}")
            return None
    
    def generate_memoir(self, chat_history: List[Dict[str, str]]) -> Optional[str]:
        """
        基于聊天记录生成回忆录文章
        
        Args:
            chat_history: 聊天历史 [{"role": "user/ai", "content": "..."}]
            
        Returns:
            生成的回忆录文章
        """
        try:
            return self.client.generate_memoir(chat_history)
        except Exception as e:
            print(f"回忆录生成失败: {e}")
            return None
    
    def generate_followup_question(self, chat_history: List[Dict[str, str]]) -> Optional[str]:
        """
        基于聊天历史生成追问问题
        
        Args:
            chat_history: 聊天历史
            
        Returns:
            生成的追问问题
        """
        try:
            return self.client.generate_followup_question(chat_history)
        except Exception as e:
            print(f"追问问题生成失败: {e}")
            return None
    
    def get_available_models(self) -> Dict[str, Dict[str, str]]:
        """
        获取可用的模型列表
        
        Returns:
            模型分类字典
        """
        return {
            'chat': self.client.CHAT_MODELS,
            'asr': self.client.ASR_MODELS,
            'tts': self.client.TTS_MODELS,
            'voices': self.client.TTS_VOICES
        }


# 创建服务实例
ai_service = AIService()
