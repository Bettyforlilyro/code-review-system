import uuid

from sqlalchemy.dialects.postgresql import UUID

from . import db


# 测试套件模型
class TestSuite(db.Model):
    __tablename__ = 'test_suites'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 测试套件基本信息
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('projects.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, default=db.func.now())
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)

    # 生成测试套件任务相关
    # 保留前端请求原始参数，可以为空，建议还是带参数生成用例更加精准；否则由Agent自动分析生成各方面用例
    generation_parameters = db.Column(db.JSON)
    # 测试套件生成任务状态，pending/generating/completed/failed
    generation_status = db.Column(db.String(20), nullable=False, default='pending')
    # 测试套件最新一次执行状态，not_started/running/completed/failed
    last_execution_status = db.Column(db.String(20), nullable=False, default='not_started')

    # 统计信息
    test_case_count = db.Column(db.Integer, nullable=False, default=0)

    # 关系：关联测试用例，间接关联测试用例执行结果
    # 一个用例可能有多次执行结果记录，但是一个测试套件的一次汇总执行结果只关心当前这一批用例的这一次用例结果
    # 一个测试套件可能会被多次执行，对应多个测试报告
    test_cases = db.relationship('TestCase', backref='test_suite',
                                 lazy='dynamic', cascade='all')
    test_reports = db.relationship('TestReport', backref='test_suite',
                                   lazy='dynamic', cascade='all')

    # 索引
    __table_args__ = (
        db.Index('idx_test_suite_project_status', 'project_id', 'generation_status'),
        db.Index('idx_test_suite_project_execution_status', 'project_id', 'execution_status'),
        db.Index('idx_test_suite_project_created_at', 'project_id', 'created_at')
    )


# 测试用例模型
class TestCase(db.Model):
    __tablename__ = 'test_cases'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_suite_id = db.Column(UUID(as_uuid=True), db.ForeignKey('test_suites.id'), nullable=False)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('projects.id'), nullable=False)

    # 测试用例基本信息
    case_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, default=db.func.now())
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    # 测试目标，function/performance/stress/security/reliability
    test_type = db.Column(db.String(50), nullable=False, default='function')
    # 测试考虑角度方法，分为boundary, equivalence, condition-table, etc.
    test_consideration_method = db.Column(db.String(50), nullable=False)
    # 保存最后一次执行状态，方便快速查询过滤，pass/fail/error/skipped
    last_execution_status = db.Column(db.String(20), nullable=True)
    last_execution_time = db.Column(db.Float, nullable=True)    # 执行时长
    last_executed_at = db.Column(db.TIMESTAMP, nullable=True)   # 执行时间

    # 目标代码信息
    target_code_file_path = db.Column(db.String(500), nullable=False)
    target_element_type = db.Column(db.String(50), nullable=False)      # function, class, method, etc.
    target_element_name = db.Column(db.String(100), nullable=False)
    target_code = db.Column(db.Text, nullable=False)
    setup_code = db.Column(db.Text)
    teardown_code = db.Column(db.Text)

    # 测试输入输出参数
    test_inputs = db.Column(db.JSON)        # 输入参数
    expected_outputs = db.Column(db.JSON)   # 期望输出参数
    assertions = db.Column(db.JSON)         # 断言逻辑

    # 关系
    execution_results = db.relationship('TestExecutionResult', backref='test_case',
                                        lazy='dynamic', cascade='all')

    # 索引
    __table_args__ = (
        db.Index('idx_test_case_project_suit_id', 'project_id', 'test_suite_id'),
        db.Index('idx_test_case_suit_id', 'test_suite_id'),
        db.Index('idx_test_case_status', 'last_execution_status'),  # 按照最后一次执行结果快速过滤，高频
        db.Index('idx_test_case_project_created_at', 'project_id', 'created_at')
    )


# 测试执行结果模型
class TestExecutionResult(db.Model):
    __tablename__ = 'test_execution_results'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_case_id = db.Column(UUID(as_uuid=True), db.ForeignKey('test_cases.id'), nullable=False)
    test_report_id = db.Column(UUID(as_uuid=True), db.ForeignKey('test_reports.id'), nullable=False)

    # 执行结果信息
    execution_status = db.Column(db.String(20), nullable=False)     # pass/fail/error/skipped
    execution_time = db.Column(db.Float, nullable=False)    # 执行耗时
    executed_at = db.Column(db.TIMESTAMP, default=db.func.now())
    stack_trace = db.Column(db.Text)    # 执行失败情况下的错误堆栈（可选）
    assertion_results = db.Column(db.JSON)      # 每个断言的结果

    # 索引
    __table_args__ = (
        # 复合索引，查询某个用例的最新执行结果可能比较高频，另外支持单独按照用例查询所有测试执行结果
        db.Index('idx_test_execution_result_case_executed_at', 'test_case_id', 'executed_at'),
        db.Index('idx_test_execution_status', 'execution_status'),     # 记录可能非常多，当前评估需要索引
        db.Index('idx_test_execution_time', 'executed_at'),
        db.Index('idx_test_execution_result_report_id', 'test_report_id')
    )


# 测试报告模型
class TestReport(db.Model):
    __tablename__ = 'test_reports'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_suite_id = db.Column(UUID(as_uuid=True), db.ForeignKey('test_suites.id'), nullable=False)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('projects.id'), nullable=False)

    # 测试报告信息
    generated_at = db.Column(db.TIMESTAMP, default=db.func.now())
    # 整体覆盖率
    line_coverage = db.Column(db.Float, nullable=True)
    branch_coverage = db.Column(db.Float, nullable=True)
    function_coverage = db.Column(db.Float, nullable=True)
    # 文件级覆盖率详情
    file_coverage = db.Column(db.JSON)
    # 覆盖缺口分析
    coverage_gaps = db.Column(db.JSON)
    # 测试用例执行结果
    passed_case_count = db.Column(db.Integer, nullable=False)       # 通过用例数
    failed_case_count = db.Column(db.Integer, nullable=False)       # 失败用例数
    skipped_case_count = db.Column(db.Integer, nullable=False)      # 跳过用例数
    total_execution_time = db.Column(db.Float, nullable=False)      # 执行总时长
    total_test_case_count = db.Column(db.Integer, nullable=False)   # 总用例数

    # 关系
    test_execution_results = db.relationship('TestExecutionResult', backref='test_report',
                                             lazy='dynamic', cascade='all')

    # 索引
    __table_args__ = (
        db.Index('idx_test_report_project_suit_id', 'project_id', 'test_suite_id'),
        db.Index('idx_test_report_suit', 'test_suite_id')
    )

