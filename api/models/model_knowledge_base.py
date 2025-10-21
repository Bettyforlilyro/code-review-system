import uuid

from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector

from . import db


# 知识库文档模型
class KnowledgeDocument(db.Model):
    __tablename__ = 'knowledge_documents'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('projects.id'), nullable=False)

    # 文档基本信息，标题和摘要（摘要可选）
    title = db.Column(db.String(256), nullable=False)
    abstract = db.Column(db.Text, nullable=True)
    abstract_embedding = db.Column(Vector(), nullable=True)
    # 文档所属项目阶段，可选project_plan/requirement_analysis/design/implementation/testing/deployment/maintenance, etc.
    document_project_phase = db.Column(db.String(32), nullable=False)   # 不能为空值
    # 文档类型，可选spec/code_comment/api_doc/BRD/SRS/test_plan/deploy_guide/other, etc.
    document_type = db.Column(db.String(32), nullable=True)     # 可以为空值，根据其他信息检索文档
    # 文档来源，可选字段
    source_type = db.Column(db.String(32), nullable=True)   # uploaded/code_extracted/generated
    source_file_path = db.Column(db.String(500), nullable=True)

    # 统计信息
    total_chunks = db.Column(db.Integer, nullable=False, default=0)
    total_tokens = db.Column(db.Integer, nullable=False, default=0)

    # 元数据
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.TIMESTAMP, default=db.func.now())
    updated_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True)
    updated_at = db.Column(db.TIMESTAMP, default=db.func.now())

    # 关系
    chunks = db.relationship('DocumentChunk', backref='knowledge_document',
                             lazy='dynamic', cascade='all')

    # 索引
    __table_args__ = (
        db.Index('idx_knowledge_document_project_type', 'project_id', 'document_type'),
        db.Index('idx_knowledge_document_project_phase', 'project_id', 'document_project_phase'),
        db.Index('idx_knowledge_document_project_updated_at', 'project_id', 'updated_at'),
        db.Index('idx_knowledge_document_project_id_abstract_embedding', 'abstract_embedding', postgresql_using='ivfflat'),
    )


# 文档分块模型
class DocumentChunk(db.Model):
    __tablename__ = 'document_chunks'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    knowledge_document_id = db.Column(UUID(as_uuid=True), db.ForeignKey('knowledge_documents.id'), nullable=False)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('projects.id'), nullable=False)
    chunk_text = db.Column(db.Text, nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)     # 分块在文档中的索引，0, ..., total_chunks-1
    embedding = db.Column(Vector(), nullable=False)

    # 元数据
    token_count = db.Column(db.Integer, nullable=False)     # 分块的token数
    word_count = db.Column(db.Integer, nullable=False)      # 分块的word数
    created_at = db.Column(db.TIMESTAMP, default=db.func.now())

    # 索引
    __table_args__ = (
        db.Index('idx_document_chunk_project_id', 'project_id'),
        db.Index('idx_document_chunk_document_idx', 'knowledge_document_id', 'chunk_index'),
        db.Index('idx_document_chunk_embedding', 'embedding', postgresql_using='ivfflat')   # 轻量级数据库，暂不使用HNSW索引
    )


# 高质量问答对模型
class HighQualityQAPair(db.Model):
    __tablename__ = 'high_quality_qa_pairs'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('projects.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    question_embedding = db.Column(Vector(), nullable=False)

    # 分类和标签，方便快速检索，允许空值
    category = db.Column(db.String(50), nullable=True)
    tags = db.Column(db.JSON, nullable=True)

    # 质量评估和反馈，用于不断优化，后续可能还会修改，允许空值
    quality_score = db.Column(db.Float, nullable=True)      # 质量评分，0-1
    user_feedback_score = db.Column(db.Float, nullable=True)    # 用户反馈评分，0-1
    feedback_count = db.Column(db.Integer, nullable=True, default=0)       # 反馈次数，次数越高置信度越高
    usage_count = db.Column(db.Integer, nullable=True, default=0)          # 被使用次数，次数越高置信度越高

    # 来源信息
    source_type = db.Column(db.String(20), nullable=True)   # 可选qa_interaction/qa_session/human_added
    source_interaction_id = db.Column(UUID(as_uuid=True), db.ForeignKey('qa_session_interactions.id'), nullable=True)
    source_session_id = db.Column(UUID(as_uuid=True), db.ForeignKey('qa_sessions.id'), nullable=True)
    approved_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.TIMESTAMP, nullable=True)
    status = db.Column(db.String(20), nullable=True)    # 可选pending/approved/rejected

    # 元数据
    created_at = db.Column(db.TIMESTAMP, default=db.func.now())
    updated_at = db.Column(db.TIMESTAMP, default=db.func.now(), on_update=db.func.now())

    # 索引
    __table_args__ = (
        db.Index('idx_high_quality_qa_pair_project_status', 'project_id', 'status'),
        db.Index('idx_high_quality_qa_pair_project_category', 'project_id', 'category'),
        db.Index('idx_high_quality_qa_pair_embedding', 'question_embedding', postgresql_using='ivfflat'),
        db.Index('idx_high_quality_qa_pair_quality_score', 'quality_score'),
    )


# 问答会话模型
class QASession(db.Model):
    __tablename__ = 'qa_sessions'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('projects.id'), nullable=False)

    # 会话基本信息，允许空值
    session_title = db.Column(db.String(200), nullable=True)        # 自动生成或者用户修改的会话标题
    context_files = db.Column(db.JSON, nullable=True)               # 关联的代码文件路径

    # 会话级别的用户反馈
    session_feedback_score = db.Column(db.Float, nullable=True)     # 用户反馈的本轮会话质量评分
    feedback_comment = db.Column(db.Text, nullable=True)

    # 统计信息
    interaction_count = db.Column(db.Integer, nullable=False, default=0)
    average_confidence = db.Column(db.Float, nullable=True)     # 用户反馈才有的平均置信度，因此允许空值
    positive_feedback_ratio = db.Column(db.Float, nullable=True)    # 正反馈比例

    # 元数据
    created_at = db.Column(db.TIMESTAMP, default=db.func.now())
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    last_interaction_at = db.Column(db.TIMESTAMP, nullable=True)

    # 关系
    interactions = db.relationship('QASessionInteraction', backref='qa_session',
                                   lazy='dynamic', cascade='all')

    # 索引
    __table_args__ = (
        db.Index('idx_qa_session_project_id_created_at', 'project_id', 'created_at'),
        db.Index('idx_qa_session_created_at', 'created_at'),
        db.Index('idx_qa_session_feedback', 'session_feedback_score'),
        db.Index('idx_qa_session_feedback_positive_ratio', 'positive_feedback_ratio')
    )


# 问答会话交互模型，记录问答会话中的单次交互
class QASessionInteraction(db.Model):
    __tablename__ = 'qa_session_interactions'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    qa_session_id = db.Column(UUID(as_uuid=True), db.ForeignKey('qa_sessions.id'), nullable=False)
    project_id = db.Column(UUID(as_uuid=True), db.ForeignKey('projects.id'), nullable=False)

    # 问题处理
    original_question = db.Column(db.Text, nullable=False)
    optimized_question = db.Column(db.Text, nullable=True)      # 可选，优化后的问题
    question_embedding = db.Column(Vector(), nullable=False)

    # 检索信息，都允许空值
    retrieved_qa_pairs = db.Column(db.JSON, nullable=True)      # 记录检索到的问答对ID以及相关置信评分
    retrieved_chunks = db.Column(db.JSON, nullable=True)        # 记录检索到的分段ID以及相关置信评分
    retrieved_documents = db.Column(db.JSON, nullable=True)     # 记录检索到的文档ID以及相关置信评分

    # 生成的回答
    generated_answer = db.Column(db.Text, nullable=False)
    confidence_score = db.Column(db.Float, nullable=True)       # 生成回答的置信度，0~1
    reasoning_process = db.Column(db.Text, nullable=True)       # 思考过程，可选

    # 用户反馈信息，单次交互级别，允许空值
    user_feedback_score = db.Column(db.Float, nullable=True)    # 用户反馈的会话质量评分，0~1
    feedback_comment = db.Column(db.Text, nullable=True)

    # 元数据
    asked_at = db.Column(db.TIMESTAMP, default=db.func.now())
    answered_at = db.Column(db.TIMESTAMP, nullable=True)

    # 索引
    __table_args__ = (
        db.Index('idx_qa_session_interaction_project_id_asked_at', 'project_id', 'asked_at'),
        db.Index('idx_qa_session_interaction_project_id_user_feedback_score', 'project_id', 'user_feedback_score'),
        db.Index('idx_qa_session_interaction_project_id_confidence_score', 'project_id', 'confidence_score'),
        db.Index('idx_qa_session_interaction_project_id_embedding', 'project_id', 'question_embedding', postgresql_using='ivfflat')
    )
