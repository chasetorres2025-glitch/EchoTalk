from flask import Blueprint, request
from datetime import datetime
from app.utils.database import mysql_db, mongo_db
from app.utils.ai_service import ai_service
from app.utils.response import success, error

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/message', methods=['POST'])
def send_message():
    """
    发送消息并获取AI回复
    """
    data = request.get_json()
    session_id = data.get('session_id')
    open_id = data.get('open_id')
    message = data.get('message')

    if not all([session_id, open_id, message]):
        return error('缺少必要参数')

    try:
        # 将 session_id 转换为整数，确保类型一致
        session_id = int(session_id)
        
        # 查询用户ID
        user_sql = 'SELECT id FROM user WHERE open_id = %s'
        user = mysql_db.execute(user_sql, (open_id,), fetchone=True)

        if not user:
            return error('用户不存在', code=404)

        user_id = user['id']

        # 保存用户消息到MongoDB
        chat_collection = mongo_db.get_collection('chat_log')
        user_msg_doc = {
            'user_id': user_id,
            'session_id': session_id,
            'role': 'user',
            'content': message,
            'timestamp': datetime.now(),
            'voice_relation_id': None
        }
        chat_collection.insert_one(user_msg_doc)

        # 获取会话历史
        history = list(chat_collection.find(
            {'session_id': session_id},
            {'_id': 0, 'role': 1, 'content': 1}
        ).sort('timestamp', -1).limit(10))

        history.reverse()

        # 调用AI生成回复
        ai_response = ai_service.generate_followup_question(history)

        if not ai_response:
            ai_response = '嗯，我在听，您继续讲。'

        # 保存AI回复
        ai_msg_doc = {
            'user_id': user_id,
            'session_id': session_id,
            'role': 'ai',
            'content': ai_response,
            'timestamp': datetime.now(),
            'voice_relation_id': None
        }
        chat_collection.insert_one(ai_msg_doc)

        return success({
            'ai_response': ai_response
        })

    except Exception as e:
        print(f'发送消息失败: {e}')
        return error('发送消息失败')

@chat_bp.route('/history/<int:session_id>', methods=['GET'])
def get_chat_history(session_id):
    """
    获取聊天记录
    """
    try:
        chat_collection = mongo_db.get_collection('chat_log')
        messages = list(chat_collection.find(
            {'session_id': session_id},
            {'_id': 0}
        ).sort('timestamp', 1))

        # 转换时间格式
        for msg in messages:
            if 'timestamp' in msg:
                msg['timestamp'] = msg['timestamp'].isoformat()

        return success({
            'messages': messages
        })

    except Exception as e:
        print(f'获取聊天记录失败: {e}')
        return error('获取聊天记录失败')
