import hashlib
import os
import time
from datetime import timedelta
from functools import wraps

from flask import request, g, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token

from api.models.model_user import User, db
from api.gateway import bp as auth_bp


# JWT配置
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY',
                           (hashlib.md5((str(time.time())).encode('utf-8') + os.urandom(16))).hexdigest())
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)


def has_permission(required_permission: str):
    """
    权限校验装饰器
    使用示例：
        @bp.route('/reviews', methods=['POST'])
        @has_permission('review:write')
        def create_review():
            ...
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # 验证用户是否存在（防删除账户后仍用旧 token）
                from flask_jwt_extended import get_jwt_identity, get_jwt
                user_id = get_jwt_identity()
                user = User.query.filter_by(id=user_id).first()
                if not user:
                    return jsonify({"error": "User not found"}), 401

                # 检查权限
                user_permissions = user.get_permissions()
                if required_permission not in user_permissions or 'all' not in user_permissions:
                    return jsonify({"error": "Insufficient permissions"}), 403

            except Exception as e:
                return jsonify({"error": "Authentication failed"}), 401

            return f(*args, **kwargs)

        return decorated_function

    return decorator


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({"error": "Username already exists"}), 409

    user = User(username=username, email=email, role='normal_user')
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    # 注册完后立即跳转登录，也需要返回token
    token = set_current_user(user)
    # 如果需要刷新 token，也可以创建
    refresh_token = create_refresh_token(identity=user.id)
    return jsonify(({
        "access_token": token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": 3600,  # 60 分钟，目的是为了告诉前端
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "permissions": user.get_permissions()
        }
    })), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = set_current_user(user)
    # 如果需要刷新 token，也可以创建
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify({
        "access_token": token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": 3600,  # 60 分钟，目的是为了告诉前端
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "permissions": user.get_permissions()
        }
    }), 200


def set_current_user(user):
    # 注入用户上下文并返回有效token
    g.current_user = user.username
    g.user_id = user.id
    g.role = user.role
    token = create_access_token(
        identity=str(user.id),
        expires_delta=JWT_ACCESS_TOKEN_EXPIRES,
        additional_claims={
            'username': user.username,
            'email': user.email
        }
    )
    return token
