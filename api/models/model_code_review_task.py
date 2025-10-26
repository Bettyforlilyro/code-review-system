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
    code_file_id = db.Column(UUID(as_uuid=True),
                             db.ForeignKey('code_files.id', ondelete='CASCADE'),
                             nullable=False)
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
    review_task_scope = db.Column(db.String(64), nullable=False)  # project/directory/file
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
# 这个表关联两个问题表：跨文件问题表cross_file_issues、单文件问题表single_file_issues，哪一个有效取决于review_task_scope
# 如果是单文件审查结果，则code_file_version_id代表对应的文件版本，同时使用单文件问题表single_file_issues
# 如果是整个项目或者文件夹的审查结果，请根据关系定义获取所有的code_file_versions，同时使用跨文件问题表cross_file_issues
class ReviewResult(db.Model):
    __tablename__ = 'review_results'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 外键
    review_task_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('review_tasks.id', ondelete='cascade'),
        nullable=False
    )
    review_task_scope = db.Column(db.String(64), nullable=False)    # project/directory/file
    # 如果是整个项目或者文件夹的任务（即review_task_scope为project/directory），则code_file_version_id为None，
    # 此时请根据关系定义查找对应的ReviewTask，然后通过关联表VersionTaskAssociation获取所有的code_file_version_id
    code_file_version_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('code_file_versions.id', ondelete='cascade'),
        nullable=True
    )

    # 统计信息
    total_issues_count = db.Column(db.Integer, nullable=False, default=0)
    # 按问题严重程度
    critical_issues_count = db.Column(db.Integer, nullable=False, default=0)
    major_issues_count = db.Column(db.Integer, nullable=False, default=0)
    medium_issues_count = db.Column(db.Integer, nullable=False, default=0)
    suggestion_issues_count = db.Column(db.Integer, nullable=False, default=0)
    # 按问题类型
    functional_issues_count = db.Column(db.Integer, nullable=False, default=0)
    bad_smell_issues_count = db.Column(db.Integer, nullable=False, default=0)
    security_issues_count = db.Column(db.Integer, nullable=False, default=0)
    performance_issues_count = db.Column(db.Integer, nullable=False, default=0)
    maintainability_issues_count = db.Column(db.Integer, nullable=False, default=0)
    reliability_issues_count = db.Column(db.Integer, nullable=False, default=0)

    # 结果元数据
    analysis_time = db.Column(db.Float, nullable=True)      # 分析任务耗时，单位ms
    result_metadata = db.Column(db.JSON, nullable=True)     # 存储额外的分析数据
    completed_at = db.Column(db.TIMESTAMP, default=db.func.now())

    # 关系
    # ReviewTask与ReviewResult是一对一关系，ReviewTask是ReviewResult的根源，删除ReviewTask时，会级联删除ReviewResult
    review_task = db.relationship('ReviewTask',
                                  # 在ORM层自动创建反向关系，支持从ReviewTask中查询所有关联的ReviewResult
                                  backref=db.backref('review_result', uselist=False, cascade='all, delete-orphan'))

    # 辅助方法，获取代码文件元数据
    @property
    def code_files(self):
        if self.review_task_scope == 'file':    # 单个文件只需要返回单条code_file记录
            return CodeFile.query.filter(
                CodeFile.id == CodeFileVersion.code_file_id
            ).filter(
                CodeFileVersion.id == self.code_file_version_id
            ).first()
        else:
            # 先根据ReviewTask关联的VersionTaskAssociation获取所有的code_file_version_id
            # 然后根据所有的code_file_version_id查询对应的code_file
            # 使用数据库JOIN操作一次查询就可以了
            return CodeFile.query.join(CodeFileVersion, CodeFileVersion.code_file_id == CodeFile.id) \
                .join(VersionTaskAssociation, VersionTaskAssociation.version_id == CodeFileVersion.id) \
                .filter(VersionTaskAssociation.review_task_id == self.review_task_id) \
                .distinct().all()

    # 索引和约束
    __table_args__ = (
        # 根据completed_at查询
        db.Index('idx_review_result_completed_at', 'completed_at'),
        # 按照任务+分析完成时间查询，建立复合索引，由于复合索引支持前导列匹配，不需要单独为review_task_id创建单独索引
        db.Index('idx_review_result_task_id_completed_at', 'review_task_id', 'completed_at'),
        # 按照任务范围查询
        db.Index('idx_review_result_scope', 'review_task_scope'),
    )


class SingleFileIssue(db.Model):
    __tablename__ = 'single_file_issues'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_result_id = db.Column(UUID(as_uuid=True), db.ForeignKey('review_results.id'), nullable=False)
    code_file_version_id = db.Column(UUID(as_uuid=True), db.ForeignKey('code_file_versions.id'), nullable=False)

    # 问题基本信息
    issue_type = db.Column(db.String(64), nullable=False)
    severity = db.Column(db.String(64), nullable=False)
    line_begin = db.Column(db.Integer, nullable=True)
    line_end = db.Column(db.Integer, nullable=True)
    line_number = db.Column(db.Integer, nullable=True)
    code_snippet = db.Column(db.Text, nullable=True)
    problem_description = db.Column(db.Text, nullable=False)
    solution_suggestion = db.Column(db.Text, nullable=True)

    # 问题评估以及状态跟踪
    confidence_score = db.Column(db.Float, nullable=False, default=1.0)     # 置信度
    status = db.Column(db.String(20), nullable=False)       # 问题闭环情况，open/in_progress/closed/won't resolve
    assigned_to = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True)   # 处理责任人
    relevance_to = db.Column(db.String(64), nullable=False)     # manager/architect/developer
    is_change_related = db.Column(db.Boolean, nullable=True, default=False)
    introduced_version_id = db.Column(UUID(as_uuid=True), db.ForeignKey('code_file_versions.id'), nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=db.func.now())
    resolved_at = db.Column(db.TIMESTAMP, nullable=True)

    # 关系
    code_file_version = db.relationship('CodeFileVersion', foreign_keys=[code_file_version_id],
                                        # 在ORM层自动创建反向关系，支持从CodeFileVersion中查询所有关联的SingleFileIssue
                                        backref=db.backref('single_file_issues', lazy='dynamic', cascade='delete'))
    introduced_version = db.relationship('CodeFileVersion', foreign_keys=[introduced_version_id])

    # 索引和约束
    __table_args__ = (
        # 根据review_result_id查询，当前预估高频
        db.Index('idx_single_file_issue_result_id', 'review_result_id'),
        # 根据code_file_version_id查询，当前预估高频
        db.Index('idx_single_file_issue_version_id', 'code_file_version_id'),
        # 根据status查询
        db.Index('idx_single_file_issue_status', 'status'),
        # 根据severity查询
        db.Index('idx_single_file_issue_severity', 'severity'),
        # 根据issue_type查询
        db.Index('idx_single_file_issue_type', 'issue_type'),
        # 根据confidence_score排序查询
        db.Index('idx_single_file_issue_confidence_score', 'confidence_score')
    )


class CrossFileIssue(db.Model):
    __tablename__ = 'cross_file_issues'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_result_id = db.Column(UUID(as_uuid=True), db.ForeignKey('review_results.id'), nullable=False)

    # 问题基本信息
    issue_type = db.Column(db.String(64), nullable=False)   # 问题大类：architecture/design/dependency/performance/security
    severity = db.Column(db.String(64), nullable=False)
    category = db.Column(db.String(64), nullable=True)     # 问题小类：circular dependency/god object/long method
    problem_description = db.Column(db.Text, nullable=False)
    solution_suggestion = db.Column(db.Text, nullable=False)
    impact_analysis = db.Column(db.Text, nullable=False)    # 问题影响分析

    # 问题评估以及状态跟踪
    confidence_score = db.Column(db.Float, nullable=False, default=1.0)
    status = db.Column(db.String(20), nullable=False)   # 问题闭环情况，open/in_progress/closed/won't resolve
    assigned_to = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True)   # 处理责任人
    relevance_to = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.TIMESTAMP, default=db.func.now())
    resolved_at = db.Column(db.TIMESTAMP, nullable=True)

    # 关系
    affected_files = db.relationship('CrossFileIssueAffectedFile', backref='cross_file_issue',
                                     lazy='dynamic', cascade='delete')

    # 索引
    __table_args__ = (
        db.Index('idx_cross_file_issue_result_id', 'review_result_id'),
        db.Index('idx_cross_file_issue_status', 'status'),
        db.Index('idx_cross_file_issue_severity', 'severity'),
        db.Index('idx_cross_file_issue_type_category', 'issue_type', 'category'),
        db.Index('idx_cross_file_issue_category', 'category'),
        db.Index('idx_cross_file_issue_confidence_score', 'confidence_score')
    )


class CrossFileIssueAffectedFile(db.Model):
    __tablename__ = 'cross_file_issue_affected_files'

    cross_file_issue_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('cross_file_issues.id', ondelete='cascade'),
        primary_key=True,
        nullable=False)
    code_file_version_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('code_file_versions.id', ondelete='cascade'),
        primary_key=True,
        nullable=False
    )
    issue_metadata = db.Column(db.JSON, nullable=True)      # 这个文件在这个跨文件综合问题中的描述相关信息

    # 关系
    code_file_version = db.relationship(
        'CodeFileVersion',
        foreign_keys=[code_file_version_id],
        backref=db.backref('cross_file_issue_affected_files', lazy='dynamic', cascade='delete')
    )

    # 索引
    __table_args__ = (
        db.Index('idx_cross_file_issue_affected_file_file_id', 'code_file_version_id'),
    )
