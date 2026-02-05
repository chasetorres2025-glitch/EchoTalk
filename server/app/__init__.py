from flask import Flask
from flask_cors import CORS
from config import get_config
from app.utils.database import mongo_db

def create_app(env=None):
    """
    应用工厂函数
    :param env: 环境类型 (development/production/testing)
    :return: Flask应用实例
    """
    import os
    # 获取项目根目录（server目录）
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(project_root, 'templates')
    static_dir = os.path.join(project_root, 'static')
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)

    # 加载配置
    config = get_config(env)
    app.config.from_object(config)

    # 初始化MongoDB
    mongo_db.init_app(app)

    # 启用跨域 - 开发环境使用宽松配置
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "*"],
            "supports_credentials": False
        }
    })

    # 注册蓝图
    from app.routes.auth import auth_bp
    from app.routes.session import session_bp
    from app.routes.chat import chat_bp
    from app.routes.article import article_bp
    from app.routes.voice import voice_bp
    from app.routes.test_voice import test_voice_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(session_bp, url_prefix='/api/session')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(article_bp, url_prefix='/api/article')
    app.register_blueprint(voice_bp, url_prefix='/api/voice')
    app.register_blueprint(test_voice_bp)

    # 健康检查
    @app.route('/health')
    def health_check():
        return {'code': 0, 'message': 'OK', 'env': app.config.get('DEBUG')}

    # 数据库连接检查
    @app.route('/health/db')
    def db_health_check():
        try:
            # 检查MySQL连接
            from app.utils.database import mysql_db
            mysql_db.execute('SELECT 1')

            # 检查MongoDB连接
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
