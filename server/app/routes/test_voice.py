"""
语音对话测试模块
提供Web界面进行真人语音对话测试
"""
import os
import tempfile
import uuid
from flask import Blueprint, render_template, request, jsonify, current_app
from werkzeug.utils import secure_filename
from ..utils.ai_service import ai_service

# 创建蓝图
test_voice_bp = Blueprint('test_voice', __name__, url_prefix='/test-voice')

# 允许上传的音频格式
ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'm4a', 'webm', 'ogg'}


def allowed_audio_file(filename):
    """检查文件是否为允许的音频格式"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS


@test_voice_bp.route('/')
def index():
    """语音测试页面"""
    return render_template('test_voice.html')


@test_voice_bp.route('/api/asr', methods=['POST'])
def speech_to_text():
    """
    语音识别API
    接收音频文件，返回识别文字
    """
    try:
        # 检查是否有文件
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': '没有上传音频文件'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'success': False, 'error': '文件名为空'}), 400
        
        # 保存临时文件
        temp_dir = tempfile.gettempdir()
        unique_id = str(uuid.uuid4())
        filename = secure_filename(f"{unique_id}_{audio_file.filename}")
        filepath = os.path.join(temp_dir, filename)
        
        audio_file.save(filepath)
        
        try:
            # 调用语音识别
            text = ai_service.speech_to_text(filepath)
            
            if text:
                return jsonify({
                    'success': True,
                    'text': text
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '语音识别失败，未能识别出文字'
                }), 500
        finally:
            # 清理临时文件
            if os.path.exists(filepath):
                os.remove(filepath)
                
    except Exception as e:
        current_app.logger.error(f"语音识别错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@test_voice_bp.route('/api/chat', methods=['POST'])
def chat():
    """
    AI对话API
    接收用户消息，返回AI回复
    """
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'success': False, 'error': '缺少message参数'}), 400
        
        user_message = data['message']
        chat_history = data.get('history', [])
        
        # 构建消息列表
        messages = [
            {"role": "system", "content": "你是一位亲切的AI助手，正在和一位老人聊天。请用温暖、耐心的语气回复。"}
        ]
        
        # 添加历史对话
        for msg in chat_history[-6:]:  # 只保留最近6轮
            messages.append({"role": "user", "content": msg['user']})
            messages.append({"role": "assistant", "content": msg['ai']})
        
        # 添加当前消息
        messages.append({"role": "user", "content": user_message})
        
        # 调用AI对话
        response = ai_service.chat(messages, temperature=0.8)
        
        if response:
            return jsonify({
                'success': True,
                'response': response
            })
        else:
            return jsonify({
                'success': False,
                'error': 'AI对话失败'
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"AI对话错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@test_voice_bp.route('/api/tts', methods=['POST'])
def text_to_speech():
    """
    语音合成API
    接收文字，返回音频文件
    """
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'success': False, 'error': '缺少text参数'}), 400
        
        text = data['text']
        
        # 生成临时文件路径
        temp_dir = tempfile.gettempdir()
        unique_id = str(uuid.uuid4())
        output_path = os.path.join(temp_dir, f"{unique_id}_tts.mp3")
        
        # 调用语音合成
        result = ai_service.text_to_speech(text, output_path=output_path)
        
        if result and os.path.exists(output_path):
            # 读取音频文件并返回
            with open(output_path, 'rb') as f:
                audio_data = f.read()
            
            # 清理临时文件
            os.remove(output_path)
            
            from flask import send_file
            import io
            
            return send_file(
                io.BytesIO(audio_data),
                mimetype='audio/mpeg',
                as_attachment=False,
                download_name='response.mp3'
            )
        else:
            return jsonify({
                'success': False,
                'error': '语音合成失败'
            }), 500
            
    except Exception as e:
        current_app.logger.error(f"语音合成错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@test_voice_bp.route('/api/models', methods=['GET'])
def get_models():
    """获取可用的模型和音色列表"""
    try:
        models = ai_service.get_available_models()
        return jsonify({
            'success': True,
            'models': models
        })
    except Exception as e:
        current_app.logger.error(f"获取模型列表错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
