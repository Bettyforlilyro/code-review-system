from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import UUID
import uuid


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='normal_user')  # admin, normal_user
    register_at = db.Column(db.TIMESTAMP, default=db.func.now())

    # 后台基础权限（如果是项目群总监admin具有所有权限，如果是normal_user则按照项目进行权限管理）
    ROLE_PERMISSIONS = {
        'normal_user': ['normal'],
        'admin': ['all']
    }

    def set_password(self, password):
        self.password_hash = generate_password_hash(
            password,
            method='pbkdf2:sha256:150000',
            salt_length=8
        )

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_permissions(self):
        return self.ROLE_PERMISSIONS.get(self.role, [])
