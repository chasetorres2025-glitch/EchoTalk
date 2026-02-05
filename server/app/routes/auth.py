from flask import Blueprint, request
import requests
from app.utils.database import mysql_db
from app.utils.response import success, error

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    微信登录
    1. 获取微信code，换取openid
    2. 查询或创建用户
    3. 返回用户信息和openid
    """
    data = request.get_json()
    code = data.get('code')

    if not code:
        return error('缺少code参数')

    try:
        # 调用微信接口获取openid
        # 实际项目中需要从配置读取appid和secret
        appid = 'your-appid'  # 从配置读取
        secret = 'your-secret'  # 从配置读取

        # 这里模拟微信登录，实际项目中调用微信API
        # wx_url = f'https://api.weixin.qq.com/sns/jscode2session?appid={appid}&secret={secret}&js_code={code}&grant_type=authorization_code'
        # response = requests.get(wx_url)
        # wx_data = response.json()
        # openid = wx_data.get('openid')

        # 模拟openid
        import hashlib
        openid = hashlib.md5(code.encode()).hexdigest()[:28]

        # 查询用户是否存在
        user_sql = 'SELECT * FROM user WHERE open_id = %s'
        user = mysql_db.execute(user_sql, (openid,), fetchone=True)

        if not user:
            # 创建新用户
            nickname = f'用户{openid[-6:]}'
            insert_sql = '''
                INSERT INTO user (open_id, nickname, create_time, update_time)
                VALUES (%s, %s, NOW(), NOW())
            '''
            mysql_db.execute(insert_sql, (openid, nickname))

            # 重新查询用户信息
            user = mysql_db.execute(user_sql, (openid,), fetchone=True)

        return success({
            'openId': openid,
            'userInfo': {
                'id': user['id'],
                'nickname': user['nickname'],
                'dialect': user.get('dialect', ''),
                'phone': user.get('phone', '')
            }
        })

    except Exception as e:
        print(f'登录失败: {e}')
        return error('登录失败')
