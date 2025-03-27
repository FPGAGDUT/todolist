# auth.py
from flask import request, jsonify, g
import sqlite3
import os
import datetime
import uuid
import hashlib
import jwt
import functools

# JWT密钥，实际应用请使用环境变量等安全方式存储
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-please-change-in-production')
TOKEN_EXPIRY = 24 * 60 * 60  # 24小时

def hash_password(password):
    """对密码进行哈希处理"""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ':' + key.hex()

def verify_password(stored_password, provided_password):
    """验证密码"""
    salt_hex, key_hex = stored_password.split(':')
    salt = bytes.fromhex(salt_hex)
    stored_key = bytes.fromhex(key_hex)
    new_key = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
    return stored_key == new_key

def generate_token(user_id):
    """生成JWT令牌"""
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=TOKEN_EXPIRY)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def decode_token(token):
    """解码JWT令牌"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None  # 令牌过期
    except jwt.InvalidTokenError:
        return None  # 无效令牌

def login_required(f):
    """验证用户登录状态的装饰器"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({"error": "未提供认证令牌"}), 401
        
        try:
            # 获取Bearer令牌
            token = auth_header.split(' ')[1]
            user_id = decode_token(token)
            
            if not user_id:
                return jsonify({"error": "无效或过期的令牌"}), 401
                
            # 将用户ID存储在Flask的g对象中，供视图函数使用
            g.user_id = user_id
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": f"认证错误: {str(e)}"}), 401
            
    return decorated_function