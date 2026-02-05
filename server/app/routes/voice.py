from flask import Blueprint, request
import os
import uuid
from datetime import datetime
from app.utils.database import mysql_db
from app.utils.response import success, error
from app.utils.bailian_client import bailian_client

voice_bp = Blueprint('voice', __name__)

# 临时存储路径
UPLOAD_FOLDER = 'uploads/voice'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@voice_bp.route('/upload', methods=['POST'])
def upload_voice():
    """
    上传语音文件
    1. 保存语音文件到本地
    2. 调用语音识别API转文字
    3. 保存语音记录到数据库
    4. 返回识别结果
    """
    if 'voice' not in request.files:
        return error('没有上传语音文件')

    voice_file = request.files['voice']
    session_id = request.form.get('session_id')
    open_id = request.form.get('open_id')

    if not all([session_id, open_id]):
        return error('缺少必要参数')

    try:
        # 生成文件名
        file_ext = voice_file.filename.split('.')[-1] if '.' in voice_file.filename else 'webm'
        file_name = f"{uuid.uuid4().hex}.{file_ext}"
        file_path = os.path.join(UPLOAD_FOLDER, file_name)

        # 保存文件到本地
        voice_file.save(file_path)

        # 查询用户ID
        user_sql = 'SELECT id FROM user WHERE open_id = %s'
        user = mysql_db.execute(user_sql, (open_id,), fetchone=True)

        if not user:
            return error('用户不存在', code=404)

        user_id = user['id']

        # 调用语音识别API
        recognized_text = bailian_client.speech_to_text(file_path)

        if not recognized_text:
            return error('语音识别失败', code=500)

        # 上传到对象存储（模拟）
        voice_url = f"https://your-bucket.oss-cn-hangzhou.aliyuncs.com/voice/{file_name}"

        # 保存语音记录到MySQL
        insert_sql = '''
            INSERT INTO voice_relation (user_id, session_id, voice_url, voice_type, create_time)
            VALUES (%s, %s, %s, 0, NOW())
        '''
        mysql_db.execute(insert_sql, (user_id, session_id, voice_url))

        # 获取新创建的语音记录ID
        voice_sql = '''
            SELECT id FROM voice_relation
            WHERE session_id = %s AND voice_url = %s
            ORDER BY create_time DESC
            LIMIT 1
        '''
        voice_record = mysql_db.execute(voice_sql, (session_id, voice_url), fetchone=True)
        voice_id = voice_record['id']

        return success({
            'voice_id': voice_id,
            'voice_url': voice_url,
            'text': recognized_text
        })

    except Exception as e:
        print(f'上传语音失败: {e}')
        import traceback
        traceback.print_exc()
        return error('上传语音失败')


@voice_bp.route('/tts', methods=['POST'])
def text_to_speech():
    """
    文字转语音
    """
    data = request.get_json()
    text = data.get('text')
    voice = data.get('voice', 'longanyang')  # 默认音色

    if not text:
        return error('缺少text参数')

    try:
        # 生成临时文件路径
        audio_file = f"{uuid.uuid4().hex}.mp3"
        audio_path = os.path.join(UPLOAD_FOLDER, audio_file)

        # 调用语音合成API
        result = bailian_client.text_to_speech(
            text=text,
            voice=voice,
            output_path=audio_path
        )

        if not result:
            return error('语音合成失败', code=500)

        # 返回音频文件
        from flask import send_file
        return send_file(
            audio_path,
            mimetype='audio/mpeg',
            as_attachment=False,
            download_name='tts.mp3'
        )

    except Exception as e:
        print(f'语音合成失败: {e}')
        import traceback
        traceback.print_exc()
        return error('语音合成失败')


@voice_bp.route('/models', methods=['GET'])
def get_voice_models():
    """
    获取支持的语音模型列表
    """
    return success({
        'asr_models': bailian_client.ASR_MODELS,
        'tts_models': bailian_client.TTS_MODELS,
        'tts_voices': bailian_client.TTS_VOICES
    })
