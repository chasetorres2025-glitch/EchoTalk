"""
实时语音对话处理模块
使用 WebSocket 实现实时语音交互
"""
import json
import base64
import time
import threading
import websocket
from datetime import datetime
from app.utils.bailian_client import bailian_client
from app.utils.database import mysql_db, mongo_db
from app.utils.ai_service import ai_service

active_sessions = {}

def handle_websocket(ws, session_id, open_id):
    """
    处理 WebSocket 连接
    """
    print(f"[WS] 新连接: session_id={session_id}, open_id={open_id}")
    
    try:
        session_id = int(session_id)
    except (TypeError, ValueError):
        print(f"[WS] 无效的会话ID: {session_id}")
        ws.send(json.dumps({'type': 'error', 'message': '无效的会话ID'}))
        return
    
    user_sql = 'SELECT id FROM user WHERE open_id = %s'
    user = mysql_db.execute(user_sql, (open_id,), fetchone=True)
    
    if not user:
        print(f"[WS] 用户不存在: {open_id}")
        ws.send(json.dumps({'type': 'error', 'message': '用户不存在'}))
        return
    
    user_id = user['id']
    print(f"[WS] 用户ID: {user_id}")
    
    accumulated_text = ""
    last_audio_time = time.time()
    is_running = True
    asr_ws = None
    
    def process_ai_response(text):
        nonlocal is_running
        if not is_running or not text.strip():
            return
            
        print(f"[AI] 处理用户输入: {text}")
        
        try:
            ws.send(json.dumps({'type': 'user_speech', 'text': text}))
            
            chat_collection = mongo_db.get_collection('chat_log')
            user_msg_doc = {
                'user_id': user_id,
                'session_id': session_id,
                'role': 'user',
                'content': text,
                'timestamp': datetime.now(),
                'voice_relation_id': None
            }
            chat_collection.insert_one(user_msg_doc)
            
            history = list(chat_collection.find(
                {'session_id': session_id},
                {'_id': 0, 'role': 1, 'content': 1}
            ).sort('timestamp', -1).limit(10))
            history.reverse()
            
            ai_response = ai_service.generate_followup_question(history)
            
            if not ai_response:
                ai_response = '嗯，我在听，您继续讲。'
            
            ai_msg_doc = {
                'user_id': user_id,
                'session_id': session_id,
                'role': 'ai',
                'content': ai_response,
                'timestamp': datetime.now(),
                'voice_relation_id': None
            }
            chat_collection.insert_one(ai_msg_doc)
            
            ws.send(json.dumps({'type': 'ai_response', 'text': ai_response}))
            
            try:
                import tempfile
                import os
                
                audio_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
                audio_path = audio_file.name
                audio_file.close()
                
                result = bailian_client.text_to_speech(
                    text=ai_response,
                    output_path=audio_path
                )
                
                if result and os.path.exists(audio_path):
                    with open(audio_path, 'rb') as f:
                        audio_data = f.read()
                        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                        ws.send(json.dumps({'type': 'ai_audio', 'audio': audio_base64}))
                    
                    os.unlink(audio_path)
                    ws.send(json.dumps({'type': 'ai_audio_complete', 'message': '语音合成完成'}))
                else:
                    print(f"[TTS] 语音合成失败")
            except Exception as tts_err:
                print(f"[TTS] 语音合成异常: {tts_err}")
                
        except Exception as e:
            print(f"[AI] 处理失败: {e}")
    
    def on_asr_message(ws_asr, message):
        nonlocal accumulated_text, last_audio_time
        try:
            result = json.loads(message)
            print(f"[ASR] 收到消息: {result}")
            
            if 'payload' in result:
                payload = result['payload']
                if 'sentence' in payload:
                    sentence = payload['sentence']
                    text = sentence.get('text', '')
                    if text:
                        print(f"[ASR] 识别文本: {text}")
                        accumulated_text = text
                        last_audio_time = time.time()
        except Exception as e:
            print(f"[ASR] 解析消息失败: {e}")
    
    def on_asr_error(ws_asr, error):
        print(f"[ASR] 错误: {error}")
    
    def on_asr_close(ws_asr, close_status_code, close_msg):
        print(f"[ASR] 连接关闭: {close_status_code} {close_msg}")
    
    def check_silence():
        nonlocal accumulated_text, last_audio_time, is_running
        
        while is_running:
            time.sleep(0.3)
            
            if not is_running:
                return
                
            current_time = time.time()
            time_since_last_audio = current_time - last_audio_time
            
            if accumulated_text and time_since_last_audio >= 1.5:
                print(f"[VAD] 检测到静音，处理文本: {accumulated_text}")
                text_to_process = accumulated_text
                accumulated_text = ""
                
                threading.Thread(target=process_ai_response, args=(text_to_process,), daemon=True).start()
    
    try:
        import dashscope
        api_key = bailian_client.api_key
        
        asr_url = f"wss://dashscope.aliyuncs.com/api-ws/v1/inference/asr/paraformer-realtime-v2?api-key={api_key}"
        
        print(f"[ASR] 连接到阿里云ASR服务...")
        
        asr_ws = websocket.WebSocketApp(
            asr_url,
            on_message=on_asr_message,
            on_error=on_asr_error,
            on_close=on_asr_close
        )
        
        def on_asr_open(ws_asr):
            print(f"[ASR] 连接已打开")
            header = {
                "header": {
                    "action": "start",
                    "streaming": "duplex"
                },
                "payload": {
                    "format": "pcm",
                    "sample_rate": 16000,
                    "language_hints": ["zh", "en"]
                }
            }
            ws_asr.send(json.dumps(header))
            print(f"[ASR] 已发送开始消息")
        
        asr_ws.on_open = on_asr_open
        
        asr_thread = threading.Thread(target=asr_ws.run_forever, daemon=True)
        asr_thread.start()
        
        time.sleep(0.5)
        
        ws.send(json.dumps({'type': 'session_started', 'message': '实时对话已开始'}))
        
        silence_thread = threading.Thread(target=check_silence, daemon=True)
        silence_thread.start()
        
        print(f"[WS] 实时对话已开始")
        
    except Exception as e:
        print(f"[ASR] 创建连接失败: {e}")
        import traceback
        traceback.print_exc()
        ws.send(json.dumps({'type': 'error', 'message': '创建语音识别连接失败'}))
        return
    
    try:
        audio_frame_count = 0
        while True:
            try:
                message = ws.receive()
            except Exception as recv_err:
                print(f"[WS] 接收消息异常: {recv_err}")
                break
                
            if message is None:
                print(f"[WS] 收到空消息，连接关闭")
                break
            
            try:
                data = json.loads(message)
                msg_type = data.get('type')
                
                if msg_type == 'audio_frame':
                    audio_base64 = data.get('audio')
                    if audio_base64 and asr_ws:
                        audio_data = base64.b64decode(audio_base64)
                        audio_frame_count += 1
                        last_audio_time = time.time()
                        if audio_frame_count % 10 == 0:
                            print(f"[WS] 收到音频帧 #{audio_frame_count}, 大小: {len(audio_data)} bytes")
                        
                        audio_message = {
                            "header": {
                                "action": "send_audio"
                            },
                            "payload": {
                                "audio": audio_base64
                            }
                        }
                        asr_ws.send(json.dumps(audio_message))
                
                elif msg_type == 'stop_session':
                    print(f"[WS] 收到停止会话请求")
                    if accumulated_text:
                        process_ai_response(accumulated_text)
                        accumulated_text = ""
                    break
                
                elif msg_type == 'user_interrupt':
                    print(f"[WS] 收到打断请求")
                    ws.send(json.dumps({'type': 'interrupt_ack', 'message': '已停止AI播放'}))
                    
            except json.JSONDecodeError:
                print(f"[WS] 无效的JSON消息")
                
    except Exception as e:
        print(f"[WS] 连接异常: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        is_running = False
        if asr_ws:
            try:
                asr_ws.close()
            except:
                pass
        print(f"[WS] 连接关闭: session_id={session_id}")
