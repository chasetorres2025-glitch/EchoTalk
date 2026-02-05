from flask import Blueprint, request
from app.utils.database import mysql_db
from app.utils.response import success, error

session_bp = Blueprint('session', __name__)

@session_bp.route('/create', methods=['POST'])
def create_session():
    """
    创建新的聊天会话
    """
    data = request.get_json()
    open_id = data.get('open_id')

    if not open_id:
        return error('缺少open_id参数')

    try:
        # 查询用户ID
        user_sql = 'SELECT id FROM user WHERE open_id = %s'
        user = mysql_db.execute(user_sql, (open_id,), fetchone=True)

        if not user:
            return error('用户不存在', code=404)

        user_id = user['id']

        # 创建会话
        insert_sql = '''
            INSERT INTO session (user_id, start_time, status, article_id)
            VALUES (%s, NOW(), 0, NULL)
        '''
        mysql_db.execute(insert_sql, (user_id,))

        # 获取新创建的会话ID
        session_sql = '''
            SELECT id FROM session
            WHERE user_id = %s
            ORDER BY start_time DESC
            LIMIT 1
        '''
        session = mysql_db.execute(session_sql, (user_id,), fetchone=True)

        return success({
            'session_id': session['id'],
            'user_id': user_id
        })

    except Exception as e:
        print(f'创建会话失败: {e}')
        return error('创建会话失败')

@session_bp.route('/<int:session_id>', methods=['GET'])
def get_session(session_id):
    """
    获取会话信息
    """
    try:
        session_sql = 'SELECT * FROM session WHERE id = %s'
        session = mysql_db.execute(session_sql, (session_id,), fetchone=True)

        if not session:
            return error('会话不存在', code=404)

        return success({
            'session': session
        })

    except Exception as e:
        print(f'获取会话失败: {e}')
        return error('获取会话失败')

@session_bp.route('/<int:session_id>/end', methods=['POST'])
def end_session(session_id):
    """
    结束会话
    """
    try:
        update_sql = '''
            UPDATE session
            SET end_time = NOW()
            WHERE id = %s
        '''
        mysql_db.execute(update_sql, (session_id,))

        return success(message='会话已结束')

    except Exception as e:
        print(f'结束会话失败: {e}')
        return error('结束会话失败')
