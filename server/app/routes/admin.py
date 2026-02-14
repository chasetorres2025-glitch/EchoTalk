from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from functools import wraps
from datetime import datetime, timedelta
from app.utils.database import mysql_db, mongo_db
import os

admin_bp = Blueprint('admin', __name__, template_folder='../templates/admin')

# 简单的登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

# 获取管理员密码（从环境变量或配置）
def get_admin_credentials():
    admin_username = os.environ.get('ADMIN_USERNAME') or 'admin'
    admin_password = os.environ.get('ADMIN_PASSWORD') or 'echotalk123'
    return admin_username, admin_password

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """管理员登录"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin_username, admin_password = get_admin_credentials()
        
        if username == admin_username and password == admin_password:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('admin.dashboard'))
        else:
            flash('用户名或密码错误', 'danger')
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    """退出登录"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@login_required
def dashboard():
    """管理后台首页 - 数据概览"""
    try:
        # 用户统计
        user_count = mysql_db.execute('SELECT COUNT(*) as count FROM user', fetchone=True)['count']
        
        # 今日新增用户
        today = datetime.now().strftime('%Y-%m-%d')
        today_user_count = mysql_db.execute(
            "SELECT COUNT(*) as count FROM user WHERE DATE(create_time) = %s",
            (today,), fetchone=True
        )['count']
        
        # 会话统计
        session_count = mysql_db.execute('SELECT COUNT(*) as count FROM session', fetchone=True)['count']
        
        # 文章统计
        article_count = mysql_db.execute('SELECT COUNT(*) as count FROM article', fetchone=True)['count']
        
        # 今日聊天记录数
        chat_collection = mongo_db.get_collection('chat_log')
        today_start = datetime.combine(datetime.now().date(), datetime.min.time())
        today_chat_count = chat_collection.count_documents({
            'timestamp': {'$gte': today_start}
        })
        
        # 最近7天用户注册趋势
        week_data = []
        for i in range(6, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            count = mysql_db.execute(
                "SELECT COUNT(*) as count FROM user WHERE DATE(create_time) = %s",
                (date,), fetchone=True
            )['count']
            week_data.append({'date': date, 'count': count})
        
        # 最新注册用户
        latest_users = mysql_db.execute(
            'SELECT id, nickname, open_id, create_time FROM user ORDER BY create_time DESC LIMIT 5'
        )
        
        # 最新文章
        latest_articles = mysql_db.execute(
            '''SELECT a.id, a.title, a.status, a.create_time, u.nickname 
               FROM article a 
               LEFT JOIN user u ON a.user_id = u.id 
               ORDER BY a.create_time DESC LIMIT 5'''
        )
        
        stats = {
            'user_count': user_count,
            'today_user_count': today_user_count,
            'session_count': session_count,
            'article_count': article_count,
            'today_chat_count': today_chat_count,
            'week_data': week_data,
            'latest_users': latest_users,
            'latest_articles': latest_articles
        }
        
        return render_template('admin/dashboard.html', stats=stats)
    
    except Exception as e:
        current_app.logger.error(f'Dashboard error: {e}')
        flash('加载数据失败', 'danger')
        return render_template('admin/dashboard.html', stats={})

@admin_bp.route('/users')
@login_required
def users():
    """用户管理列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        offset = (page - 1) * per_page
        
        # 搜索功能
        search = request.args.get('search', '')
        
        if search:
            # 搜索用户
            count_sql = "SELECT COUNT(*) as count FROM user WHERE nickname LIKE %s OR open_id LIKE %s"
            count = mysql_db.execute(count_sql, (f'%{search}%', f'%{search}%'), fetchone=True)['count']
            
            sql = '''SELECT id, nickname, open_id, dialect, phone, create_time, update_time 
                     FROM user 
                     WHERE nickname LIKE %s OR open_id LIKE %s
                     ORDER BY create_time DESC 
                     LIMIT %s OFFSET %s'''
            user_list = mysql_db.execute(sql, (f'%{search}%', f'%{search}%', per_page, offset))
        else:
            # 获取用户总数
            count = mysql_db.execute('SELECT COUNT(*) as count FROM user', fetchone=True)['count']
            
            # 获取用户列表
            sql = '''SELECT id, nickname, open_id, dialect, phone, create_time, update_time 
                     FROM user 
                     ORDER BY create_time DESC 
                     LIMIT %s OFFSET %s'''
            user_list = mysql_db.execute(sql, (per_page, offset))
        
        total_pages = (count + per_page - 1) // per_page
        
        return render_template('admin/users.html', 
                             users=user_list, 
                             page=page, 
                             total_pages=total_pages,
                             total_count=count,
                             search=search)
    
    except Exception as e:
        current_app.logger.error(f'Users list error: {e}')
        flash('加载用户列表失败', 'danger')
        return render_template('admin/users.html', users=[], page=1, total_pages=1, total_count=0, search='')

@admin_bp.route('/users/<int:user_id>')
@login_required
def user_detail(user_id):
    """用户详情"""
    try:
        # 获取用户信息
        user = mysql_db.execute(
            'SELECT * FROM user WHERE id = %s',
            (user_id,), fetchone=True
        )
        
        if not user:
            flash('用户不存在', 'warning')
            return redirect(url_for('admin.users'))
        
        # 获取用户的会话
        sessions = mysql_db.execute(
            '''SELECT s.*, 
                      (SELECT COUNT(*) FROM chat_log WHERE session_id = s.id) as message_count
               FROM session s 
               WHERE s.user_id = %s 
               ORDER BY s.start_time DESC''',
            (user_id,)
        )
        
        # 获取用户的文章
        articles = mysql_db.execute(
            'SELECT * FROM article WHERE user_id = %s ORDER BY create_time DESC',
            (user_id,)
        )
        
        return render_template('admin/user_detail.html', 
                             user=user, 
                             sessions=sessions, 
                             articles=articles)
    
    except Exception as e:
        current_app.logger.error(f'User detail error: {e}')
        flash('加载用户详情失败', 'danger')
        return redirect(url_for('admin.users'))

@admin_bp.route('/sessions')
@login_required
def sessions():
    """会话管理列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        offset = (page - 1) * per_page
        
        # 获取会话总数
        count = mysql_db.execute('SELECT COUNT(*) as count FROM session', fetchone=True)['count']
        
        # 获取会话列表
        sql = '''SELECT s.*, u.nickname, u.open_id,
                        (SELECT COUNT(*) FROM chat_log WHERE session_id = s.id) as message_count
                 FROM session s 
                 LEFT JOIN user u ON s.user_id = u.id
                 ORDER BY s.start_time DESC 
                 LIMIT %s OFFSET %s'''
        session_list = mysql_db.execute(sql, (per_page, offset))
        
        total_pages = (count + per_page - 1) // per_page
        
        return render_template('admin/sessions.html', 
                             sessions=session_list, 
                             page=page, 
                             total_pages=total_pages,
                             total_count=count)
    
    except Exception as e:
        current_app.logger.error(f'Sessions list error: {e}')
        flash('加载会话列表失败', 'danger')
        return render_template('admin/sessions.html', sessions=[], page=1, total_pages=1, total_count=0)

@admin_bp.route('/sessions/<int:session_id>')
@login_required
def session_detail(session_id):
    """会话详情"""
    try:
        # 获取会话信息
        session_info = mysql_db.execute(
            '''SELECT s.*, u.nickname, u.open_id
               FROM session s 
               LEFT JOIN user u ON s.user_id = u.id
               WHERE s.id = %s''',
            (session_id,), fetchone=True
        )
        
        if not session_info:
            flash('会话不存在', 'warning')
            return redirect(url_for('admin.sessions'))
        
        # 获取聊天记录
        chat_collection = mongo_db.get_collection('chat_log')
        messages = list(chat_collection.find(
            {'session_id': session_id},
            {'_id': 0}
        ).sort('timestamp', 1))
        
        # 转换时间格式
        for msg in messages:
            if 'timestamp' in msg and msg['timestamp']:
                msg['timestamp'] = msg['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
        
        return render_template('admin/session_detail.html', 
                             session=session_info, 
                             messages=messages)
    
    except Exception as e:
        current_app.logger.error(f'Session detail error: {e}')
        flash('加载会话详情失败', 'danger')
        return redirect(url_for('admin.sessions'))

@admin_bp.route('/sessions/<int:session_id>/delete', methods=['POST'])
@login_required
def delete_session(session_id):
    """删除会话"""
    try:
        # 删除会话
        mysql_db.execute('DELETE FROM session WHERE id = %s', (session_id,))
        
        # 删除相关聊天记录
        chat_collection = mongo_db.get_collection('chat_log')
        chat_collection.delete_many({'session_id': session_id})
        
        flash('会话已删除', 'success')
    except Exception as e:
        current_app.logger.error(f'Delete session error: {e}')
        flash('删除会话失败', 'danger')
    
    return redirect(url_for('admin.sessions'))

@admin_bp.route('/articles')
@login_required
def articles():
    """文章管理列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        offset = (page - 1) * per_page
        
        # 搜索功能
        search = request.args.get('search', '')
        
        if search:
            count_sql = "SELECT COUNT(*) as count FROM article WHERE title LIKE %s"
            count = mysql_db.execute(count_sql, (f'%{search}%',), fetchone=True)['count']
            
            sql = '''SELECT a.*, u.nickname 
                     FROM article a 
                     LEFT JOIN user u ON a.user_id = u.id
                     WHERE a.title LIKE %s
                     ORDER BY a.create_time DESC 
                     LIMIT %s OFFSET %s'''
            article_list = mysql_db.execute(sql, (f'%{search}%', per_page, offset))
        else:
            count = mysql_db.execute('SELECT COUNT(*) as count FROM article', fetchone=True)['count']
            
            sql = '''SELECT a.*, u.nickname 
                     FROM article a 
                     LEFT JOIN user u ON a.user_id = u.id
                     ORDER BY a.create_time DESC 
                     LIMIT %s OFFSET %s'''
            article_list = mysql_db.execute(sql, (per_page, offset))
        
        total_pages = (count + per_page - 1) // per_page
        
        # 状态映射
        status_map = {0: '草稿', 1: '已生成', 2: '已保存'}
        for article in article_list:
            article['status_text'] = status_map.get(article['status'], '未知')
        
        return render_template('admin/articles.html', 
                             articles=article_list, 
                             page=page, 
                             total_pages=total_pages,
                             total_count=count,
                             search=search)
    
    except Exception as e:
        current_app.logger.error(f'Articles list error: {e}')
        flash('加载文章列表失败', 'danger')
        return render_template('admin/articles.html', articles=[], page=1, total_pages=1, total_count=0, search='')

@admin_bp.route('/articles/<int:article_id>')
@login_required
def article_detail(article_id):
    """文章详情"""
    try:
        article = mysql_db.execute(
            '''SELECT a.*, u.nickname, u.open_id
               FROM article a 
               LEFT JOIN user u ON a.user_id = u.id
               WHERE a.id = %s''',
            (article_id,), fetchone=True
        )
        
        if not article:
            flash('文章不存在', 'warning')
            return redirect(url_for('admin.articles'))
        
        # 状态映射
        status_map = {0: '草稿', 1: '已生成', 2: '已保存'}
        article['status_text'] = status_map.get(article['status'], '未知')
        
        return render_template('admin/article_detail.html', article=article)
    
    except Exception as e:
        current_app.logger.error(f'Article detail error: {e}')
        flash('加载文章详情失败', 'danger')
        return redirect(url_for('admin.articles'))

@admin_bp.route('/articles/<int:article_id>/delete', methods=['POST'])
@login_required
def delete_article(article_id):
    """删除文章"""
    try:
        mysql_db.execute('DELETE FROM article WHERE id = %s', (article_id,))
        flash('文章已删除', 'success')
    except Exception as e:
        current_app.logger.error(f'Delete article error: {e}')
        flash('删除文章失败', 'danger')
    
    return redirect(url_for('admin.articles'))
