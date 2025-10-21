import logging
import time

from flask_cors import CORS
from flask_jwt_extended import JWTManager

from code_review_app import CodeReviewApp
from api.common.config.system_config import code_review_config
from api.gateway.auth import JWT_SECRET_KEY, JWT_ACCESS_TOKEN_EXPIRES

logger = logging.getLogger(__name__)


def create_flask_app() -> CodeReviewApp:
    start_time = time.perf_counter()
    app = CodeReviewApp(__name__)
    initialize_app(app)
    end_time = time.perf_counter()
    if code_review_config['logging']['level'] == 'DEBUG':
        logger.debug(f"App initialization time: {end_time - start_time}")
    return app


def initialize_app(app: CodeReviewApp):
    # 所有业务路由蓝图注册
    from api.common.extensions import (
        ext_blueprints,
    )
    extensions = [
        ext_blueprints,
    ]
    for extension in extensions:
        extension.init_app(app)

    # 在应用启动后添加这段代码，检查蓝图是否注册成功
    for rule in app.url_map.iter_rules():
        print(f"Endpoint: {rule.endpoint}, Methods: {rule.methods}, Rule: {rule.rule}")

    # 初始化JWT，用于登录鉴权
    CORS(app)
    JWTManager(app)
    app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = JWT_ACCESS_TOKEN_EXPIRES

    # 记录审计日志
    from api.gateway.logging import init_audit_log
    init_audit_log(app)

    # 初始化Flask 关系数据库DB
    from api.common.config.system_config import relation_db_config as db_config
    # 构建数据库URI
    database_uri = f"{db_config['db_type']}://{db_config['db_user']}:{db_config['db_password']}@{db_config['db_host']}:{db_config['db_port']}/{db_config['db_name']}"
    from api.models.model_user import db
    # 设置Flask-SQLAlchemy需要的配置
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 建议设置为False以避免警告
    db.init_app(app)
