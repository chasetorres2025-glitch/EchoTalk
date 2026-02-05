import pymysql
from config import Config

def init_mysql():
    """初始化MySQL数据库和表"""
    conn = pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        charset='utf8mb4'
    )

    try:
        with conn.cursor() as cursor:
            # 创建数据库
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.execute(f"USE {Config.MYSQL_DB}")

            # 创建用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    open_id VARCHAR(64) UNIQUE NOT NULL COMMENT '微信OpenID',
                    nickname VARCHAR(64) DEFAULT '' COMMENT '用户昵称',
                    dialect VARCHAR(32) DEFAULT '' COMMENT '常用方言',
                    phone VARCHAR(20) DEFAULT '' COMMENT '绑定手机号',
                    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
                    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    INDEX idx_open_id (open_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表'
            ''')

            # 创建会话表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL COMMENT '用户ID',
                    start_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
                    end_time DATETIME NULL COMMENT '结束时间',
                    status TINYINT DEFAULT 0 COMMENT '状态：0-草稿中，1-已生成文章，2-已确认保存',
                    article_id INT NULL COMMENT '关联文章ID',
                    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
                    INDEX idx_user_id (user_id),
                    INDEX idx_status (status)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会话表'
            ''')

            # 创建文章表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS article (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL COMMENT '用户ID',
                    session_id INT NOT NULL COMMENT '会话ID',
                    title VARCHAR(128) DEFAULT '' COMMENT '文章标题',
                    draft_content TEXT COMMENT '文章草稿内容',
                    final_content TEXT COMMENT '最终内容',
                    status TINYINT DEFAULT 0 COMMENT '状态：0-草稿，1-已生成，2-已保存',
                    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
                    FOREIGN KEY (session_id) REFERENCES session(id) ON DELETE CASCADE,
                    INDEX idx_user_id (user_id),
                    INDEX idx_session_id (session_id),
                    INDEX idx_status (status)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文章表'
            ''')

            # 创建语音关联表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS voice_relation (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL COMMENT '用户ID',
                    session_id INT NOT NULL COMMENT '会话ID',
                    voice_url VARCHAR(512) NOT NULL COMMENT '语音文件URL',
                    voice_type TINYINT DEFAULT 0 COMMENT '类型：0-用户发言，1-AI发言',
                    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
                    FOREIGN KEY (session_id) REFERENCES session(id) ON DELETE CASCADE,
                    INDEX idx_user_id (user_id),
                    INDEX idx_session_id (session_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='语音关联表'
            ''')

            conn.commit()
            print('MySQL数据库初始化成功！')

    except Exception as e:
        print(f'MySQL数据库初始化失败: {e}')
        conn.rollback()
    finally:
        conn.close()

def init_mongodb():
    """初始化MongoDB集合"""
    from pymongo import MongoClient

    try:
        client = MongoClient(Config.MONGO_URI)
        db = client.get_default_database()

        # 创建聊天记录集合
        chat_collection = db['chat_log']

        # 创建索引
        chat_collection.create_index([('user_id', 1)])
        chat_collection.create_index([('session_id', 1)])
        chat_collection.create_index([('timestamp', 1)])

        print('MongoDB初始化成功！')

    except Exception as e:
        print(f'MongoDB初始化失败: {e}')

if __name__ == '__main__':
    print('开始初始化数据库...')
    init_mysql()
    init_mongodb()
    print('数据库初始化完成！')
