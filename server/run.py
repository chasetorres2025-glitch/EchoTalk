from app import create_app
from config import get_config

# 获取配置
config = get_config()

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    print(f"Starting EchoTalk Server...")
    print(f"Environment: {'development' if config.DEBUG else 'production'}")
    print(f"Host: {config.HOST}")
    print(f"Port: {config.PORT}")
    print(f"MySQL: {config.MYSQL_HOST}:{config.MYSQL_PORT}/{config.MYSQL_DB}")
    print(f"MongoDB: {config.MONGO_HOST}:{config.MONGO_PORT}/{config.MONGO_DB}")

    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )
