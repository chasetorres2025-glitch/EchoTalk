def success(data=None, message='success'):
    return {
        'code': 0,
        'message': message,
        'data': data
    }

def error(message='error', code=1, data=None):
    return {
        'code': code,
        'message': message,
        'data': data
    }
