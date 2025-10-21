import uuid

from sqlalchemy.dialects.postgresql import UUID

from . import db


class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    programming_language = db.Column(db.String(50))
    local_path = db.Column(db.String(500))  # 本地项目路径
    created_at = db.Column(db.TIMESTAMP, default=db.func.now())
    owner_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))

    # 关系
    project_members = db.relationship('ProjectMember', backref='project',
                                      lazy='dynamic', cascade='delete')

    # 索引
    __table_args__ = (
        db.Index('idx_project_owner_id', 'owner_id'),
        db.Index('idx_created_at', 'created_at')
    )


class ProjectMember(db.Model):
    __tablename__ = 'project_members'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('projects.id'))
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    role = db.Column(db.String(50))  # 可选：'owner', 'architect', 'developer'
    joined_at = db.Column(db.TIMESTAMP, default=db.func.now())

    # 索引
    __table_args__ = (
        db.Index('idx_project_member_project_id_role', 'project_id', 'role'),
        db.Index('idx_project_member_user_role', 'user_id', 'role'),
        db.Index('idx_project_member_project_id_user_id', 'project_id', 'user_id')
    )
