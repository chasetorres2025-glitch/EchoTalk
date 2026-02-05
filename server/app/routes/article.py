from flask import Blueprint, request
from datetime import datetime
from app.utils.database import mysql_db, mongo_db
from app.utils.ai_service import ai_service
from app.utils.response import success, error

article_bp = Blueprint('article', __name__)

@article_bp.route('/generate', methods=['POST'])
def generate_article():
    """
    基于聊天记录生成回忆录文章
    """
    data = request.get_json()
    session_id = data.get('session_id')

    if not session_id:
        return error('缺少session_id参数')

    try:
        # 获取聊天记录
        chat_collection = mongo_db.get_collection('chat_log')
        messages = list(chat_collection.find(
            {'session_id': session_id, 'role': {'$in': ['user', 'ai']}},
            {'_id': 0, 'role': 1, 'content': 1}
        ).sort('timestamp', 1))

        if len(messages) < 2:
            return error('聊天记录太少，无法生成文章')

        # 调用AI生成文章
        article_content = ai_service.generate_memoir(messages)

        if not article_content:
            return error('文章生成失败')

        # 查询会话信息
        session_sql = 'SELECT user_id FROM session WHERE id = %s'
        session = mysql_db.execute(session_sql, (session_id,), fetchone=True)

        if not session:
            return error('会话不存在', code=404)

        user_id = session['user_id']

        # 生成标题
        title = f"{datetime.now().strftime('%Y年%m月%d日')} 回忆"

        # 保存文章到MySQL
        insert_sql = '''
            INSERT INTO article (user_id, session_id, title, draft_content, final_content, status, create_time, update_time)
            VALUES (%s, %s, %s, %s, %s, 0, NOW(), NOW())
        '''
        mysql_db.execute(insert_sql, (user_id, session_id, title, article_content, article_content))

        # 获取新创建的文章ID
        article_sql = '''
            SELECT id FROM article
            WHERE session_id = %s
            ORDER BY create_time DESC
            LIMIT 1
        '''
        article = mysql_db.execute(article_sql, (session_id,), fetchone=True)
        article_id = article['id']

        # 更新会话状态
        update_session_sql = '''
            UPDATE session
            SET status = 1, article_id = %s
            WHERE id = %s
        '''
        mysql_db.execute(update_session_sql, (article_id, session_id))

        return success({
            'article_id': article_id,
            'article': {
                'id': article_id,
                'title': title,
                'content': article_content,
                'create_time': datetime.now().isoformat()
            }
        })

    except Exception as e:
        print(f'生成文章失败: {e}')
        return error('生成文章失败')

@article_bp.route('/<int:article_id>', methods=['GET'])
def get_article(article_id):
    """
    获取文章详情
    """
    try:
        article_sql = '''
            SELECT id, user_id, session_id, title, draft_content, final_content, status, create_time, update_time
            FROM article WHERE id = %s
        '''
        article = mysql_db.execute(article_sql, (article_id,), fetchone=True)

        if not article:
            return error('文章不存在', code=404)

        return success({
            'id': article['id'],
            'title': article['title'],
            'content': article['final_content'] or article['draft_content'],
            'status': article['status'],
            'create_time': article['create_time'].isoformat() if article['create_time'] else None,
            'update_time': article['update_time'].isoformat() if article['update_time'] else None
        })

    except Exception as e:
        print(f'获取文章失败: {e}')
        return error('获取文章失败')

@article_bp.route('/<int:article_id>', methods=['PUT'])
def update_article(article_id):
    """
    更新文章内容
    """
    data = request.get_json()
    content = data.get('content')

    if not content:
        return error('缺少content参数')

    try:
        update_sql = '''
            UPDATE article
            SET final_content = %s, update_time = NOW()
            WHERE id = %s
        '''
        mysql_db.execute(update_sql, (content, article_id))

        return success(message='文章已更新')

    except Exception as e:
        print(f'更新文章失败: {e}')
        return error('更新文章失败')

@article_bp.route('/<int:article_id>/save', methods=['POST'])
def save_article(article_id):
    """
    保存文章（确认最终版本）
    """
    try:
        # 更新文章状态
        update_article_sql = '''
            UPDATE article
            SET status = 2, update_time = NOW()
            WHERE id = %s
        '''
        mysql_db.execute(update_article_sql, (article_id,))

        # 更新会话状态
        session_sql = 'SELECT session_id FROM article WHERE id = %s'
        article = mysql_db.execute(session_sql, (article_id,), fetchone=True)

        if article:
            update_session_sql = '''
                UPDATE session
                SET status = 2
                WHERE id = %s
            '''
            mysql_db.execute(update_session_sql, (article['session_id'],))

        return success(message='文章已保存')

    except Exception as e:
        print(f'保存文章失败: {e}')
        return error('保存文章失败')

@article_bp.route('/user/<open_id>', methods=['GET'])
def get_user_articles(open_id):
    """
    获取用户的所有文章
    """
    try:
        # 查询用户ID
        user_sql = 'SELECT id FROM user WHERE open_id = %s'
        user = mysql_db.execute(user_sql, (open_id,), fetchone=True)

        if not user:
            return error('用户不存在', code=404)

        user_id = user['id']

        # 查询文章列表
        articles_sql = '''
            SELECT id, title, draft_content, final_content, status, create_time
            FROM article
            WHERE user_id = %s
            ORDER BY create_time DESC
        '''
        articles = mysql_db.execute(articles_sql, (user_id,))

        # 处理文章数据
        article_list = []
        for article in articles:
            content = article['final_content'] or article['draft_content'] or ''
            preview = content[:100] + '...' if len(content) > 100 else content

            article_list.append({
                'id': article['id'],
                'title': article['title'],
                'preview': preview,
                'status': article['status'],
                'create_time': article['create_time'].isoformat() if article['create_time'] else None
            })

        return success({
            'articles': article_list
        })

    except Exception as e:
        print(f'获取文章列表失败: {e}')
        return error('获取文章列表失败')
