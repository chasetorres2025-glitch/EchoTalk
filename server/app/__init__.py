from flask import Flask, request
from flask_cors import CORS
from config import get_config
from app.utils.database import mongo_db
import json

def create_app(env=None):
    """
    应用工厂函数
    :param env: 环境类型 (development/production/testing)
    :return: Flask应用实例
    """
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(project_root, 'templates')
    static_dir = os.path.join(project_root, 'static')
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)

    config = get_config(env)
    app.config.from_object(config)

    mongo_db.init_app(app)

    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "*"],
            "supports_credentials": False
        }
    })

    from app.routes.auth import auth_bp
    from app.routes.session import session_bp
    from app.routes.chat import chat_bp
    from app.routes.article import article_bp
    from app.routes.voice import voice_bp
    from app.routes.test_voice import test_voice_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(session_bp, url_prefix='/api/session')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(article_bp, url_prefix='/api/article')
    app.register_blueprint(voice_bp, url_prefix='/api/voice')
    app.register_blueprint(test_voice_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    @app.route('/health')
    def health_check():
        return {'code': 0, 'message': 'OK', 'env': app.config.get('DEBUG')}

    @app.route('/health/db')
    def db_health_check():
        try:
            from app.utils.database import mysql_db
            mysql_db.execute('SELECT 1')
            mongo_db.client.admin.command('ping')
            return {
                'code': 0,
                'message': 'Database connections OK',
                'mysql': 'connected',
                'mongodb': 'connected'
            }
        except Exception as e:
            return {
                'code': 1,
                'message': f'Database connection failed: {str(e)}',
                'mysql': 'disconnected',
                'mongodb': 'disconnected'
            }, 500

    return app


def websocket_app(environ, start_response):
    """
    WebSocket 应用 - 处理 WebSocket 连接
    """
    import sys
    from geventwebsocket import WebSocketError
    
    path = environ.get('PATH_INFO', '')
    
    if path.startswith('/ws/realtime/'):
        print(f"[WS] 收到WebSocket请求: {path}", file=sys.stderr, flush=True)
        
        ws = environ.get('wsgi.websocket')
        if ws:
            parts = path.split('/')
            if len(parts) >= 5:
                session_id = parts[3]
                open_id = parts[4]
                print(f"[WS] session_id={session_id}, open_id={open_id}", file=sys.stderr, flush=True)
                
                from app.routes.realtime import handle_websocket
                handle_websocket(ws, session_id, open_id)
                return []
    
    return None
