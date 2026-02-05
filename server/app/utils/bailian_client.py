"""
阿里云百炼平台客户端封装
支持对话、语音识别、语音合成等功能
文档: https://bailian.console.aliyun.com
"""
import os
import json
import base64
import requests
import tempfile
import threading
from typing import Optional, List, Dict, Union, Generator
from flask import current_app


class BailianClient:
    """阿里云百炼平台客户端"""
    
    # 支持的模型列表
    CHAT_MODELS = {
        'qwen-turbo': '通义千问Turbo - 快速响应',
        'qwen-plus': '通义千问Plus - 均衡性能',
        'qwen-max': '通义千问Max - 最强能力',
        'qwen-max-latest': '通义千问Max最新版',
        'deepseek-r1': 'DeepSeek-R1 - 推理模型',
        'deepseek-v3': 'DeepSeek-V3 - 通用模型',
    }
    
    ASR_MODELS = {
        'paraformer-v2': 'Paraformer V2 - 文件识别',
        'paraformer-realtime-v2': 'Paraformer实时版',
    }
    
    TTS_MODELS = {
        'cosyvoice-v1': 'CosyVoice V1 - 超自然语音',
        'cosyvoice-v2': 'CosyVoice V2 - 增强版',
        'cosyvoice-v3-flash': 'CosyVoice V3 Flash - 极速版',
        'cosyvoice-v3-plus': 'CosyVoice V3 Plus - 专业版',
        'sambert-v1': 'Sambert - 标准语音',
    }
    
    # CosyVoice 音色列表
    TTS_VOICES = {
        'longanyang': '安阳 - 标准男声 (v3推荐)',
        'longxiaochun': '小春 - 温柔女声 (v2)',
        'longxiaoxia': '小夏 - 活泼女声 (v2)',
        'longxiaocheng': '小成 - 成熟男声 (v2)',
        'longxiaobai': '小白 - 清澈女声 (v2)',
        'longxiaotian': '小田 - 温暖男声 (v2)',
        'longwan': '小婉 - 标准女声',
        'longshu': '书书 - 知性女声',
        'longshuo': '硕硕 - 阳光男声',
        'longjing': '婧婧 - 甜美女声',
        'longmiao': '喵喵 - 可爱女声',
    }
    
    def __init__(self):
        self._api_key = None
        self._base_url = None
        self._chat_model = None
        self._asr_model = None
        self._tts_model = None
        self._tts_voice = None
    
    @property
    def api_key(self) -> str:
        """获取API密钥"""
        if self._api_key is None:
            self._api_key = current_app.config.get('ALIYUN_API_KEY', '')
        return self._api_key
    
    @property
    def base_url(self) -> str:
        """获取基础URL"""
        if self._base_url is None:
            self._base_url = current_app.config.get('ALIYUN_API_URL', 
                'https://dashscope.aliyuncs.com/compatible-mode/v1')
        return self._base_url
    
    @property
    def chat_model(self) -> str:
        """获取对话模型"""
        if self._chat_model is None:
            self._chat_model = current_app.config.get('CHAT_MODEL', 'qwen-turbo')
        return self._chat_model
    
    @property
    def asr_model(self) -> str:
        """获取语音识别模型"""
        if self._asr_model is None:
            self._asr_model = current_app.config.get('ASR_MODEL', 'paraformer-v2')
        return self._asr_model
    
    @property
    def tts_model(self) -> str:
        """获取语音合成模型"""
        if self._tts_model is None:
            self._tts_model = current_app.config.get('TTS_MODEL', 'cosyvoice-v3-flash')
        return self._tts_model
    
    @property
    def tts_voice(self) -> str:
        """获取语音合成音色"""
        if self._tts_voice is None:
            self._tts_voice = current_app.config.get('TTS_VOICE', 'longanyang')
        return self._tts_voice
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       model: Optional[str] = None,
                       temperature: float = 0.7,
                       max_tokens: int = 2000,
                       stream: bool = False) -> Union[str, Generator[str, None, None]]:
        """
        对话补全
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            model: 模型名称，默认使用配置中的模型
            temperature: 温度参数 (0-2)
            max_tokens: 最大生成token数
            stream: 是否流式输出
            
        Returns:
            非流式：生成的文本
            流式：文本生成器
        """
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            'model': model or self.chat_model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'stream': stream
        }
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                stream=stream,
                timeout=60
            )
            response.raise_for_status()
            
            if stream:
                return self._parse_stream_response(response)
            else:
                result = response.json()
                return result.get('choices', [{}])[0].get('message', {}).get('content', '')
                
        except requests.exceptions.RequestException as e:
            print(f"对话请求失败: {e}")
            return None
    
    def _parse_stream_response(self, response) -> Generator[str, None, None]:
        """解析流式响应"""
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    try:
                        json_data = json.loads(data)
                        delta = json_data.get('choices', [{}])[0].get('delta', {})
                        content = delta.get('content', '')
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue
    
    def _upload_file_to_bailian(self, file_path: str, model_name: str) -> Optional[str]:
        """
        上传文件到百炼临时存储，获取临时URL
        使用 dashscope SDK 的文件上传功能
        
        Args:
            file_path: 本地文件路径
            model_name: 模型名称
            
        Returns:
            临时URL (oss://...)，失败返回None
        """
        print(f"[ASR] 开始上传文件到百炼临时存储...")
        
        try:
            import dashscope
            from dashscope import Files
            
            # 设置 API Key
            dashscope.api_key = self.api_key
            
            # 使用 SDK 上传文件
            print(f"[ASR] 使用 SDK 上传文件...")
            file_response = Files.upload(file_path=file_path, purpose='file-extraction')
            
            print(f"[ASR] 文件上传响应: status_code={file_response.status_code}")
            print(f"[ASR] 文件上传响应 output: {file_response.output}")
            
            if file_response.status_code != 200:
                print(f"[ASR] 文件上传失败: {getattr(file_response, 'message', 'unknown')}")
                return None
            
            # 获取 file_id
            uploaded_files = file_response.output.get('uploaded_files', []) if hasattr(file_response, 'output') else []
            if not uploaded_files:
                print("[ASR] 错误: 未获取到上传文件信息")
                return None
            
            file_id = uploaded_files[0].get('file_id')
            print(f"[ASR] 文件上传成功，file_id: {file_id}")
            
            # 获取文件详情以获取 URL
            print(f"[ASR] 获取文件 URL...")
            file_detail = Files.get(file_id=file_id)
            print(f"[ASR] 文件详情响应: {file_detail.output}")
            
            if file_detail.status_code == 200:
                file_url = file_detail.output.get('url') if hasattr(file_detail, 'output') else None
                print(f"[ASR] 文件 URL: {file_url[:80] if file_url else 'None'}...")
                return file_url
            else:
                print(f"[ASR] 获取文件详情失败")
                return None
            
        except ImportError as ie:
            print(f"[ASR] 导入错误: {ie}")
            print("[ASR] 未安装 dashscope SDK，请运行: pip install dashscope")
            return None
        except Exception as e:
            print(f"[ASR] 上传文件异常: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def speech_to_text(self, 
                      audio_file_path: str,
                      model: Optional[str] = None,
                      format: str = 'mp3',
                      sample_rate: int = 16000) -> Optional[str]:
        """
        语音识别 (Paraformer)
        使用阿里云百炼 Transcription API - 异步任务方式
        
        Args:
            audio_file_path: 音频文件路径
            model: 模型名称
            format: 音频格式 (mp3, wav, pcm)
            sample_rate: 采样率
            
        Returns:
            识别出的文本，失败返回None
        """
        print(f"[ASR] 开始语音识别，文件: {audio_file_path}")
        
        try:
            import dashscope
            from dashscope.audio.asr import Transcription
            from urllib import request
            
            # 检查文件是否存在
            if not os.path.exists(audio_file_path):
                print(f"[ASR] 错误: 文件不存在 {audio_file_path}")
                return None
            
            file_size = os.path.getsize(audio_file_path)
            print(f"[ASR] 文件大小: {file_size} bytes")
            
            # 使用 paraformer-v2 模型（推荐）
            model_name = model or 'paraformer-v2'
            print(f"[ASR] 使用模型: {model_name}")
            
            # 步骤1: 上传文件获取临时URL
            file_url = self._upload_file_to_bailian(audio_file_path, model_name)
            if not file_url:
                print("[ASR] 错误: 文件上传失败")
                return None
            
            # 步骤2: 使用 dashscope SDK 提交语音识别任务
            print(f"[ASR] 步骤3: 使用 SDK 提交语音识别任务...")
            
            # 设置 API Key
            dashscope.api_key = self.api_key
            
            # 提交异步任务
            task_response = Transcription.async_call(
                model=model_name,
                file_urls=[file_url],
                language_hints=['zh', 'en']
            )
            
            print(f"[ASR] 任务提交响应: status_code={task_response.status_code}")
            
            if task_response.status_code != 200:
                print(f"[ASR] 提交任务失败: {getattr(task_response, 'message', 'unknown')}")
                return None
            
            task_id = task_response.output.get('task_id') if hasattr(task_response, 'output') else None
            print(f"[ASR] 任务提交成功，任务ID: {task_id}")
            
            if not task_id:
                print("[ASR] 错误: 未能获取任务ID")
                return None
            
            # 步骤3: 等待任务完成
            print(f"[ASR] 步骤4: 等待任务完成...")
            transcription_response = Transcription.wait(task=task_id)
            
            print(f"[ASR] 任务完成: status_code={transcription_response.status_code}")
            
            if transcription_response.status_code == 200:
                # 获取识别结果 URL
                print(f"[ASR] 任务响应 output: {transcription_response.output}")
                print(f"[ASR] 任务响应 output 类型: {type(transcription_response.output)}")
                
                # 检查任务状态
                task_status = transcription_response.output.get('task_status') if hasattr(transcription_response, 'output') else None
                print(f"[ASR] 任务状态: {task_status}")
                
                if task_status != 'SUCCEEDED':
                    print(f"[ASR] 错误: 任务未成功完成，状态: {task_status}")
                    return None
                
                results = transcription_response.output.get('results', []) if hasattr(transcription_response, 'output') else []
                print(f"[ASR] 结果列表: {results}")
                print(f"[ASR] 结果数量: {len(results)}")
                
                if results:
                    transcription_url = results[0].get('transcription_url')
                    print(f"[ASR] 转写URL: {transcription_url}")
                    if transcription_url:
                        # 下载识别结果
                        print(f"[ASR] 下载识别结果...")
                        try:
                            transcription_data = json.loads(request.urlopen(transcription_url).read().decode('utf8'))
                            print(f"[ASR] 转写数据: {transcription_data}")
                            transcripts = transcription_data.get('transcripts', [])
                            print(f"[ASR] transcripts: {transcripts}")
                            if transcripts:
                                text = transcripts[0].get('text', '')
                                print(f"[ASR] 识别成功: {text[:50] if text else 'Empty'}...")
                                return text
                            else:
                                print("[ASR] 错误: transcripts 为空")
                        except Exception as download_err:
                            print(f"[ASR] 下载结果失败: {download_err}")
                            import traceback
                            traceback.print_exc()
                            return None
                    else:
                        print("[ASR] 错误: transcription_url 为空")
                else:
                    print("[ASR] 错误: results 为空")
                return None
            else:
                print(f"[ASR] 任务执行失败: {getattr(transcription_response, 'message', 'unknown')}")
                return None
                
        except ImportError as ie:
            print(f"[ASR] 导入错误: {ie}")
            print("[ASR] 请运行: pip install dashscope")
            return None
        except FileNotFoundError:
            print(f"[ASR] 错误: 音频文件不存在: {audio_file_path}")
            return None
        except Exception as e:
            print(f"[ASR] 语音识别失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def text_to_speech(self,
                      text: str,
                      model: Optional[str] = None,
                      voice: Optional[str] = None,
                      speed: float = 1.0,
                      output_path: Optional[str] = None) -> Optional[Union[str, bytes]]:
        """
        语音合成 (CosyVoice)
        使用阿里云百炼平台的 HTTP API 进行语音合成
        
        Args:
            text: 要合成的文本
            model: 模型名称
            voice: 音色名称
            speed: 语速 (0.5-2.0)
            output_path: 输出文件路径，为None则返回音频数据
            
        Returns:
            有output_path时返回文件路径，否则返回音频字节数据
        """
        # 使用百炼平台的语音合成 API
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/tts"
        
        # 构建请求体
        payload = {
            "model": model or self.tts_model,
            "input": {
                "text": text
            },
            "parameters": {
                "voice": voice or self.tts_voice,
                "speed": speed,
                "volume": 50
            }
        }
        
        try:
            response = requests.post(
                url,
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # 检查是否有音频数据
                if 'output' in result and 'audio' in result['output']:
                    # Base64 编码的音频数据
                    audio_base64 = result['output']['audio']
                    audio_data = base64.b64decode(audio_base64)
                    
                    if output_path:
                        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
                        with open(output_path, 'wb') as f:
                            f.write(audio_data)
                        return output_path
                    else:
                        return audio_data
                else:
                    print(f"语音合成返回格式异常: {result}")
                    return None
            else:
                print(f"语音合成请求失败: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"语音合成请求失败: {e}")
            return None
    
    def text_to_speech_with_dashscope(self,
                                     text: str,
                                     model: Optional[str] = None,
                                     voice: Optional[str] = None,
                                     output_path: Optional[str] = None) -> Optional[Union[str, bytes]]:
        """
        使用 dashscope SDK 进行语音合成 (推荐方式)
        需要先安装: pip install dashscope
        
        Args:
            text: 要合成的文本
            model: 模型名称
            voice: 音色名称
            output_path: 输出文件路径
            
        Returns:
            有output_path时返回文件路径，否则返回音频字节数据
        """
        try:
            import dashscope
            from dashscope.audio.tts_v2 import SpeechSynthesizer
            
            # 设置 API Key
            dashscope.api_key = self.api_key
            
            # 创建合成器
            synthesizer = SpeechSynthesizer(
                model=model or self.tts_model,
                voice=voice or self.tts_voice
            )
            
            # 执行合成
            audio = synthesizer.call(text)
            
            if output_path:
                os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(audio)
                return output_path
            else:
                return audio
                
        except ImportError:
            print("未安装 dashscope SDK，请运行: pip install dashscope")
            return None
        except Exception as e:
            print(f"语音合成失败: {e}")
            return None
    
    def generate_memoir(self, chat_history: List[Dict[str, str]]) -> Optional[str]:
        """
        基于聊天记录生成回忆录
        
        Args:
            chat_history: 聊天历史 [{"role": "user/ai", "content": "..."}]
            
        Returns:
            生成的回忆录文章
        """
        system_prompt = """你是一位专业的回忆录撰写助手。请基于以下对话内容，生成一篇温馨、真实的回忆录文章。

要求：
1. 语言风格要贴合老年人的口语习惯，朴实、温暖
2. 保留对话中的真实情感和细节
3. 文章结构清晰，有时间、地点、人物、事件经过
4. 适当润色，但不要过度修饰，保持真实性
5. 文章字数控制在800-1500字

请直接输出文章正文，不需要标题。"""

        chat_text = "\n".join([
            f"{'老人' if msg['role'] == 'user' else 'AI'}：{msg['content']}"
            for msg in chat_history
        ])

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请根据以下对话生成回忆录：\n\n{chat_text}"}
        ]

        return self.chat_completion(messages, temperature=0.8)
    
    def generate_followup_question(self, chat_history: List[Dict[str, str]]) -> Optional[str]:
        """
        基于聊天历史生成追问问题
        
        Args:
            chat_history: 聊天历史 (最近6条)
            
        Returns:
            生成的追问问题
        """
        system_prompt = """你是一位善于引导老年人回忆过去的AI助手。请基于对话历史，生成一个自然、温和的追问问题，帮助老人挖掘更多细节。

要求：
1. 问题要具体，针对老人提到的某个人、地点或事件
2. 语气亲切、耐心，像晚辈在听长辈讲故事
3. 问题不要太复杂，一次只问一个方面
4. 如果老人已经讲得很详细，可以表示理解和共情

请只输出问题本身，不要有多余的解释。"""

        chat_text = "\n".join([
            f"{'老人' if msg['role'] == 'user' else 'AI'}：{msg['content']}"
            for msg in chat_history[-6:]  # 只取最近6条
        ])

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"对话历史：\n\n{chat_text}\n\n请生成一个追问问题："}
        ]

        return self.chat_completion(messages, temperature=0.9)


# 创建客户端实例
bailian_client = BailianClient()
