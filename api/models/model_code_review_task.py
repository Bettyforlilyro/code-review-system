import uuid

from sqlalchemy.dialects.postgresql import UUID

from . import db


# 单个代码文件模型
class CodeFile(db.Model):
    __tablename__ = 'code_files'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('projects.id'), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)   # 文件全路径
    file_size = db.Column(db.Integer, nullable=False)   # 文件大小，字节为单位
    language_type = db.Column(db.String(20), nullable=False, default='python')
    # TODO last_modified字段待删除，用版本维护各种修改时间
    last_modified = db.Column(db.TIMESTAMP, default=db.func.now())
    # 关系：一个代码文件CodeFile可能有非常多个版本CodeFileVersion(至少有一个当前最新版本的)
    # 删除CodeFile需要删除所有子CodeFileVersion记录设置cascade=delete即可
    # 取消关联某个version时这里不会删除子CodeFileVersion记录，在业务处理逻辑中需要手动删除
    # 查询最新版本时按updated_at时间排序即可，不加外键关联了否则可能会产生循环依赖
    versions = db.relationship('CodeFileVersion', backref='code_file', lazy='dynamic',
                               cascade='all')

    # 索引
    __table_args__ = (
        db.Index('idx_project_code_file_full_path', 'project_id', 'file_path'),
    )


# 代码文件版本模型
class CodeFileVersion(db.Model):
    __tablename__ = 'code_file_versions'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code_file_id = db.Column(UUID(as_uuid=True), db.ForeignKey('code_files.id'), nullable=False)
    # 最新的项目快照是哪个版本
    version_number = db.Column(db.Integer, nullable=False, default=1)
    content = db.Column(db.Text, nullable=False)
    content_hash = db.Column(db.String(64), nullable=False)
    line_added_begin = db.Column(db.Integer, nullable=True)
    line_added_end = db.Column(db.Integer, nullable=True)
    line_removed_begin = db.Column(db.Integer, nullable=True)
    line_removed_end = db.Column(db.Integer, nullable=True)
    change_description = db.Column(db.Text, nullable=True)
    updated_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    updated_at = db.Column(db.TIMESTAMP, default=db.func.now())

    # 关系：删除CodeFileVersion时需要删除所有关联的VersionTaskAssociation记录
    # 但仅取消关联某个VersionTaskAssociation时需要手动删除所有关联的VersionTaskAssociation记录---不会直接在数据库中删除，可以考虑在业务处理逻辑中需要手动删除
    task_version_links = db.relationship('VersionTaskAssociation', back_populates='code_file_version',
                                         lazy='dynamic', cascade='delete', passive_deletes=True)
    code_file_version_snapshot_links = db.relationship('CodeFileVersionSnapshotAssociation',
                                                       back_populates='code_file_version',
                                                       lazy='dynamic', cascade='delete', passive_deletes=True)

    # 辅助方法：获取所有引用此版本的 ReviewTask
    @property
    def review_tasks(self):
        return ReviewTask.query.join(VersionTaskAssociation).filter(
            VersionTaskAssociation.version_id == self.id
        )

    # 辅助方法：获取此版本的代码文件元数据
    @property
    def code_file(self):
        return CodeFile.query.get(self.code_file_id)

    # 索引
    __table_args__ = (
        # 代码文件id + 版本号是唯一索引约束（不用创建普通索引，唯一性约束会自动创建唯一索引）
        db.UniqueConstraint('code_file_id', 'version_number', name='uq_code_file_version'),
        db.Index('idx_code_file_content_hash', 'content_hash'),     # 用于快速判断文件内容是否完全相同（已存在）
        db.Index('idx_code_file_updated_at', 'updated_at')  # 按照时间排序查询，用于排序展示
    )


class CodeFileVersionSnapshotAssociation(db.Model):
    __tablename__ = 'code_file_version_snapshot_associations'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code_file_version_id = db.Column(UUID(as_uuid=True),
                                     db.ForeignKey('code_file_versions.id', ondelete='cascade'),
                                     nullable=False)
    project_version_snapshot_id = db.Column(UUID(as_uuid=True),
                                            db.ForeignKey('project_version_snapshots.id', ondelete='cascade'),
                                            nullable=False)

    # 反向关系，便于从中间表访问两端
    code_file_version = db.relationship('CodeFileVersion',
                                        back_populates='code_file_version_snapshot_links')
    project_version_snapshot = db.relationship('ProjectVersionSnapshot',
                                               back_populates='code_file_version_snapshot_links')
    # 索引
    __table_args__ = (
        db.Index('idx_code_file_version_snapshot_project_version_snapshot_id', 'project_version_snapshot_id'),
        db.Index('idx_code_file_version_snapshot_code_file_version_id', 'code_file_version_id'),
    )


class ProjectVersionSnapshot(db.Model):
    __tablename__ = 'project_version_snapshots'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.TIMESTAMP, default=db.func.now())

    # 关系：一个项目版本快照对应多个代码文件版本
    code_file_version_snapshot_links = db.relationship('CodeFileVersionSnapshotAssociation',
                                                       back_populates='project_version_snapshot',
                                                       lazy='dynamic', cascade='delete', passive_deletes=True)

    @property
    def code_file_versions(self):
        return CodeFileVersion.query.join(CodeFileVersionSnapshotAssociation).filter(
            CodeFileVersionSnapshotAssociation.project_version_snapshot_id == self.id
        )

    # 索引
    __table_args__ = (
        db.Index('idx_project_version_snapshot_project_id', 'project_id'),
        db.Index('idx_project_version_snapshot_created_at', 'created_at'),
    )


# 用户启动的审查任务模型---只与CodeFileVersion关联，多对多关系
class ReviewTask(db.Model):
    __tablename__ = 'review_tasks'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('projects.id'), nullable=False)
    review_type = db.Column(db.String(64), nullable=False)  # project/directory/file
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    # 任务信息
    task_name = db.Column(db.String(64), nullable=False)
    task_type = db.Column(db.String(64), nullable=False)    # full/quality/performance/security
    task_status = db.Column(db.String(64), nullable=False, default='pending')
    created_at = db.Column(db.TIMESTAMP, default=db.func.now())
    requirements_description = db.Column(db.Text, nullable=True)
    # 直接使用关联中间表实现多对多，关联多个CodeFileVersion。
    # 删除ReviewTask时，删除关联的所有中间表记录；同理：仅取消关联时不会自动删除需要在业务处理逻辑中手动删除
    task_version_links = db.relationship('VersionTaskAssociation', back_populates='review_task',
                                         lazy='dynamic', cascade='delete', passive_deletes=True)

    # 获取所有关联的CodeFileVersion
    @property
    def code_file_versions(self):
        return CodeFileVersion.query.join(VersionTaskAssociation).filter(
            VersionTaskAssociation.review_task_id == self.id
        )

    # 索引
    __table_args__ = (
        db.Index('idx_review_task_project_id', 'project_id', 'task_type'),  # 业务需要频繁查询整个项目中各种问题类型的ReviewTask
        db.Index('idx_review_task_created_at', 'project_id', 'created_at'),   # 按项目+创建时间查询，用于排序展示
    )


# 中间表：记录 ReviewTask 与 CodeFileVersion 的多对多关系
class VersionTaskAssociation(db.Model):
    __tablename__ = 'version_task_associations'
    review_task_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('review_tasks.id', ondelete='cascade'),
        primary_key=True
    )
    version_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('code_file_versions.id', ondelete='cascade'),
        primary_key=True
    )
    # 表示这个版本是base_version还是current_version
    version_type = db.Column(db.String(20), nullable=False, default='current_version')
    # 反向关系，方便从中间表访问两端
    review_task = db.relationship('ReviewTask', back_populates='task_version_links')
    code_file_version = db.relationship('CodeFileVersion', back_populates='task_version_links')

    # 索引
    __table_args__ = (
        db.Index('idx_vta_version_id', 'version_id'),    # 用于按照version_id查询
        # 复合主键自动创建的索引(review_task_id, version_id)已支持通过review_task_id索引高效查询
        # 因此没必要重复单独定义review_task_id索引
    )


# 针对单个代码文件版本的审查报告结果模型
# 由于前面对于多对多关系表采用的中间表VersionTaskAssociation，因此ReviewResult模型与VersionTaskAssociation是一一对应关系即可，不与其他模型耦合
class ReviewResult(db.Model):
    __tablename__ = 'review_results'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 外键到两个主表
    review_task_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('review_tasks.id', ondelete='cascade'),
        nullable=False
    )
    code_file_version_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('code_file_versions.id', ondelete='cascade'),
        nullable=False
    )

    # bad_smell/function_bug/security_issue/performance_issue/maintainability_issue
    issue_type = db.Column(db.String(64), nullable=False)
    severity = db.Column(db.String(64), nullable=False)     # critical/major/medium/suggestion
    # 针对单个CodeFile中出现的问题
    code_file_id = db.Column(UUID(as_uuid=True), db.ForeignKey('code_files.id'), nullable=False)
    # file_path = db.Column(db.String(500), db.ForeignKey('code_files.file_path'))
    line_begin = db.Column(db.Integer, nullable=False)      # 问题代码行起止
    line_end = db.Column(db.Integer, nullable=False)
    line_number = db.Column(db.Integer, nullable=False)     # 问题代码行数
    code_snippet = db.Column(db.Text, nullable=False)       # 问题代码片段
    problem_description = db.Column(db.Text, nullable=False)    # 问题描述
    solution_suggestion = db.Column(db.Text, nullable=False)    # 给出的修复建议
    confidence_score = db.Column(db.Float, nullable=False, default=1.0)     # 置信度
    process_situation = db.Column(db.String(64), nullable=False)    # 问题闭环情况，open/in_progress/closed
    relevance_to = db.Column(db.String(64), nullable=False)     # manager/architect/developer
    is_change_related = db.Column(db.Boolean, nullable=False, default=False)    # 是否某次变更引入
    introduced_version_id = db.Column(UUID(as_uuid=True), db.ForeignKey('code_file_versions.id'), nullable=True)
    result_metadata = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=db.func.now())

    # 关系
    review_task = db.relationship('ReviewTask',
                                  # 自动创建反向关系，支持从ReviewTask中查询所有关联的ReviewResult
                                  backref=db.backref('review_results', lazy='dynamic', cascade='delete'))
    code_file_version = db.relationship('CodeFileVersion', foreign_keys=[code_file_version_id],
                                        # 自动创建反向关系，支持从CodeFileVersion中查询所有关联的ReviewResult
                                        backref=db.backref('review_results', lazy='dynamic', cascade='delete'))

    # 索引和约束
    __table_args__ = (
        # 根据review_task_id查询，当前预估高频
        # db.Index('idx_review_result_task_id', 'review_task_id'),  # 复合索引支持前导列匹配，不需要单独创建普通索引
        # 根据code_file_version_id查询，当前预估高频
        db.Index('idx_review_result_version_id', 'code_file_version_id'),
        # 复合查询，当前预估高频
        db.UniqueConstraint('review_task_id', 'code_file_version_id', name='uq_review_result_task_version'),
        # 按照问题类型+严重程度查询，当前预估中低频先不创建，后期项目上线后根据查询日志多少再考虑是否新增索引
        # db.Index('idx_issue_type', 'issue_type', 'severity'),
        # 按照任务+闭环情况+严重程度查询（用于统计任务闭环情况），当前预估高频，建立复合索引，同时前导列匹配支持按照任务、任务+闭环情况高效查询
        db.Index('idx_task_process_situation_severity', 'review_task_id', 'process_situation', 'severity'),
        # 按照问题闭环情况+严重程度查询（用于跨任务计算评估整体项目风险），建立复合索引，当前预估中低频，后期项目上线后根据查询日志多少再考虑是否新增索引
        # db.Index('idx_severity_process_situation', 'process_situation', 'severity')
    )
