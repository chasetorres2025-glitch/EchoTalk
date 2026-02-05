import os
import configparser
from dotenv import load_dotenv

# 加载.env文件（敏感配置）
load_dotenv()

# 读取config.ini文件（不敏感配置）
config_ini = configparser.ConfigParser()
config_ini.read(os.path.join(os.path.dirname(__file__), 'config.ini'))


def get_ini_value(section, key, default=None, value_type=str):
    """从ini文件读取配置值"""
    try:
        if value_type == bool:
            return config_ini.getboolean(section, key)
        elif value_type == int:
            return config_ini.getint(section, key)
        elif value_type == float:
            return config_ini.getfloat(section, key)
        else:
            return config_ini.get(section, key)
    except (configparser.NoSectionError, configparser.NoOptionError):
        return default


class Config:
    """
    EchoTalk 项目统一配置文件
    敏感配置从.env读取，不敏感配置从config.ini读取
    """

    # ============================================================
    # 1. Flask 基础配置
    # ============================================================
    # 敏感：SECRET_KEY 从环境变量读取
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'echotalk-secret-key-change-me'
    # 不敏感：从config.ini读取
    DEBUG = get_ini_value('flask', 'debug', False, bool)
    PORT = get_ini_value('flask', 'port', 5050, int)
    HOST = get_ini_value('flask', 'host', '0.0.0.0')

    # ============================================================
    # 2. MySQL 数据库配置
    # ============================================================
    # 不敏感：基础连接信息
    MYSQL_HOST = get_ini_value('mysql', 'host', 'localhost')
    MYSQL_PORT = get_ini_value('mysql', 'port', 3306, int)
    MYSQL_USER = get_ini_value('mysql', 'user', 'root')
    MYSQL_DB = get_ini_value('mysql', 'db', 'echotalk')
    MYSQL_CHARSET = get_ini_value('mysql', 'charset', 'utf8mb4')
    MYSQL_POOL_SIZE = get_ini_value('mysql', 'pool_size', 10, int)
    MYSQL_POOL_TIMEOUT = get_ini_value('mysql', 'pool_timeout', 30, int)
    # 敏感：密码从环境变量读取
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or ''

    # ============================================================
    # 3. MongoDB 数据库配置
    # ============================================================
    # 不敏感：基础连接信息
    MONGO_HOST = get_ini_value('mongodb', 'host', 'localhost')
    MONGO_PORT = get_ini_value('mongodb', 'port', 27017, int)
    MONGO_DB = get_ini_value('mongodb', 'db', 'echotalk')
    # 敏感：认证信息从环境变量读取
    MONGO_USER = os.environ.get('MONGO_USER') or ''
    MONGO_PASSWORD = os.environ.get('MONGO_PASSWORD') or ''
    # MongoDB连接URI
    MONGO_URI = os.environ.get('MONGO_URI') or f'mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}'

    # ============================================================
    # 4. 微信小程序配置
    # ============================================================
    # 不敏感：API地址
    WECHAT_API_URL = get_ini_value('wechat', 'api_url', 'https://api.weixin.qq.com/sns/jscode2session')
    # 敏感：AppID和Secret从环境变量读取
    WECHAT_APPID = os.environ.get('WECHAT_APPID') or 'your-wechat-appid'
    WECHAT_SECRET = os.environ.get('WECHAT_SECRET') or 'your-wechat-secret'

    # ============================================================
    # 5. AI 大模型配置 (阿里云百炼平台)
    # ============================================================
    # 不敏感：基础配置
    AI_PROVIDER = get_ini_value('ai', 'provider', 'aliyun')
    # OpenAI兼容模式API地址
    ALIYUN_API_URL = get_ini_value('ai', 'api_url', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
    # 对话模型配置
    CHAT_MODEL = get_ini_value('ai', 'chat_model', 'qwen-turbo')
    CHAT_TEMPERATURE = get_ini_value('ai', 'chat_temperature', 0.7, float)
    CHAT_MAX_TOKENS = get_ini_value('ai', 'chat_max_tokens', 2000, int)
    CHAT_TIMEOUT = get_ini_value('ai', 'chat_timeout', 30, int)
    # 语音识别配置
    ASR_MODEL = get_ini_value('ai', 'asr_model', 'paraformer-v2')
    ASR_FORMAT = get_ini_value('ai', 'asr_format', 'mp3')
    ASR_SAMPLE_RATE = get_ini_value('ai', 'asr_sample_rate', 16000, int)
    # 语音合成配置
    TTS_MODEL = get_ini_value('ai', 'tts_model', 'cosyvoice-v1')
    TTS_VOICE = get_ini_value('ai', 'tts_voice', 'longxiaochun')
    TTS_SPEED = get_ini_value('ai', 'tts_speed', 1.0, float)
    TTS_VOLUME = get_ini_value('ai', 'tts_volume', 50, int)
    # 敏感：API密钥从环境变量读取 (百炼平台统一使用一个API Key)
    ALIYUN_API_KEY = os.environ.get('ALIYUN_API_KEY') or 'your-aliyun-api-key'

    # ============================================================
    # 6. 对象存储配置
    # ============================================================
    # 不敏感：基础配置
    STORAGE_PROVIDER = get_ini_value('storage', 'provider', 'local')
    LOCAL_STORAGE_PATH = get_ini_value('storage', 'local_path', './uploads')
    OSS_ENDPOINT = get_ini_value('storage', 'oss_endpoint', 'oss-cn-hangzhou.aliyuncs.com')
    OSS_REGION = get_ini_value('storage', 'oss_region', 'cn-hangzhou')
    COS_REGION = get_ini_value('storage', 'cos_region', 'ap-guangzhou')
    # 敏感：密钥从环境变量读取
    OSS_ACCESS_KEY_ID = os.environ.get('OSS_ACCESS_KEY_ID') or 'your-oss-access-key-id'
    OSS_ACCESS_KEY_SECRET = os.environ.get('OSS_ACCESS_KEY_SECRET') or 'your-oss-access-key-secret'
    COS_SECRET_ID = os.environ.get('COS_SECRET_ID') or 'your-cos-secret-id'
    COS_SECRET_KEY = os.environ.get('COS_SECRET_KEY') or 'your-cos-secret-key'

    # ============================================================
    # 7. 语音录制配置 (已合并到AI配置中)
    # ============================================================
    # 注意：语音识别和合成的具体配置已移至第5节 AI大模型配置
    # 百炼平台使用统一的 API Key 进行认证

    # ============================================================
    # 8. 语音录制配置
    # ============================================================
    VOICE_MAX_DURATION = get_ini_value('voice', 'max_duration', 60, int)
    VOICE_FORMAT = get_ini_value('voice', 'format', 'mp3')
    VOICE_SAMPLE_RATE = get_ini_value('voice', 'sample_rate', 16000, int)
    VOICE_BITRATE = get_ini_value('voice', 'bitrate', 48000, int)

    # ============================================================
    # 9. 业务逻辑配置
    # ============================================================
    CHAT_MAX_HISTORY = get_ini_value('business', 'chat_max_history', 50, int)
    CHAT_CONTEXT_WINDOW = get_ini_value('business', 'chat_context_window', 10, int)
    ARTICLE_MIN_MESSAGES = get_ini_value('business', 'article_min_messages', 3, int)
    ARTICLE_MAX_LENGTH = get_ini_value('business', 'article_max_length', 2000, int)
    ARTICLE_MIN_LENGTH = get_ini_value('business', 'article_min_length', 300, int)

    # ============================================================
    # 10. 日志配置
    # ============================================================
    LOG_LEVEL = get_ini_value('log', 'level', 'INFO')
    LOG_FILE = get_ini_value('log', 'file', './logs/echotalk.log')
    LOG_FORMAT = get_ini_value('log', 'format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # ============================================================
    # 11. 安全配置
    # ============================================================
    RATE_LIMIT_ENABLED = get_ini_value('security', 'rate_limit_enabled', False, bool)
    RATE_LIMIT_REQUESTS = get_ini_value('security', 'rate_limit_requests', 100, int)
    RATE_LIMIT_WINDOW = get_ini_value('security', 'rate_limit_window', 3600, int)
    MAX_CONTENT_LENGTH = get_ini_value('security', 'max_content_length', 16 * 1024 * 1024, int)


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    RATE_LIMIT_ENABLED = True


class TestingConfig(Config):
    """测试环境配置"""
    DEBUG = True
    TESTING = True
    MYSQL_DB = 'echotalk_test'
    MONGO_DB = 'echotalk_test'


# 配置映射
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env=None):
    """获取配置类"""
    if env is None:
        env = os.environ.get('FLASK_ENV') or get_ini_value('env', 'flask_env', 'development')
    return config_map.get(env, DevelopmentConfig)
