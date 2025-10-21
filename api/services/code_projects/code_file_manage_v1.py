import os.path

from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity

from api.common.utils.http_response import success_response, error_response
from api.models.model_project import Project, ProjectMember, db
from api.models.model_user import User
from api.services import bp as service_bp
from api.models.model_code_review_task import CodeFile, CodeFileVersion, ReviewTask, ReviewResult, \
    ProjectVersionSnapshot, CodeFileVersionSnapshotAssociation, VersionTaskAssociation


@service_bp.route('/projects/<project_id>/files/sync', methods=['POST'])
@jwt_required()
def sync_project_files(project_id):
    user_id = get_jwt_identity()
    if not ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first():
        return error_response("用户不是项目成员，请联系管理员添加成员！", 403, {})
    files_list = request.get_json().get("file_list")
    try:
        for file in files_list:
            is_binary = file['is_binary']
            if is_binary:   # 暂时只处理文本文件，忽略二进制文件
                continue
            file_path = file['file_path']
            file_size = file['file_size']
            file_updated_at = file['last_modified']
            file_language = file['language']
            code_file = CodeFile.query.filter_by(project_id=project_id, file_path=file_path).first()
            # 存在则更新记录
            if code_file:
                code_file.file_size = file_size
                code_file.last_modified = file_updated_at
                code_file.language_type = file_language
            else:
                # 不存在则创建
                code_file = CodeFile(
                    project_id=project_id,
                    file_path=file_path,
                    file_size=file_size,
                    last_modified=file_updated_at,
                    language_type=file_language
                )
                db.session.add(code_file)
        db.session.commit()
        return success_response(
            data={},
            message="同步成功！",
            status_code=201
        )
    except Exception as e:
        db.session.rollback()
        return error_response(
            message=f"同步失败！{str(e)}",
            status_code=500,
            data={}
        )


@service_bp.route('/projects/<project_id>/files', methods=['GET'])
@jwt_required()
def get_project_files(project_id):
    user_id = get_jwt_identity()
    if not ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first():
        return error_response("用户不是项目成员，请联系管理员添加成员！", 403, {})
    file_list = CodeFile.query.filter_by(project_id=project_id).all()
    data = []
    for file in file_list:
        data.append({
            "file_path": file.file_path,
            "file_size": str(file.file_size) + "B",
            "language_type": file.language_type,
            "last_modified": file.last_modified.isoformat(),
        })
    return success_response(
        data=data,
        message="获取文件列表成功！",
        status_code=200
    )


@service_bp.route('/projects/<project_id>/files/<version_id>', methods=['GET'])
@jwt_required()
def get_project_file_by_version(project_id, version_id):
    user_id = get_jwt_identity()
    if not ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first():
        return error_response("用户不是项目成员，请联系管理员添加成员！", 403, {})
    file_version = CodeFileVersion.query.filter_by(id=version_id).first()
    if not file_version:
        return error_response("文件不存在！", 404, {})
    return success_response(
        data={
            "version_number": file_version.version_number,
            "content": file_version.content,
            "updated_at": file_version.updated_at.isoformat(),
            "updated_by": User.query.filter_by(id=file_version.updated_by).first().username,
            "change_description": file_version.change_description,
        },
        message="获取文件版本信息成功！",
        status_code=200
    )


@service_bp.route('/projects/<project_id>/files/<file_id>', methods=['DELETE'])
@jwt_required()
def delete_project_file(project_id, file_id):
    user_id = get_jwt_identity()
    if not ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first():
        return error_response("用户不是项目成员，请联系管理员添加成员！", 403, {})
    code_file = CodeFile.query.filter_by(id=file_id).first()
    # 如果有快照引用这个文件，不允许删除

    # 如果有review_task引用这个文件，不允许删除


@service_bp.route('/projects/<project_id>/versions', methods=['POST'])
@jwt_required()
def create_project_version_snapshot(project_id):
    user_id = get_jwt_identity()
    if not ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first():
        return error_response("用户不是项目成员，请联系管理员添加成员！", 403, {})
    # 前端负责扫描所有本地文件以及内容并上传
    data = request.get_json()
    snapshot_name = data.get("name")
    snapshot_description = data.get("description")
    snapshot = ProjectVersionSnapshot(
        name=snapshot_name,
        description=snapshot_description,
        project_id=project_id,
        created_by=user_id
    )
    db.session.add(snapshot)
    db.session.commit()
    # 创建一个文件同步任务，返回快照id作为任务id
    return success_response(
        data={
            "snapshot_id": str(snapshot.id),
            "created_at": snapshot.created_at.isoformat(),
        },
        message="创建文件同步任务成功，请等待后台文件传输完成！",
        status_code=201
    )


@service_bp.route('/projects/<project_id>/versions/upload-chunk', methods=['POST'])
@jwt_required()
def upload_project_version_file_chunk(project_id):
    user_id = get_jwt_identity()
    if not ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first():
        return error_response("用户不是项目成员，请联系管理员添加成员！", 403, {})
    data = request.get_json()
    snapshot_id = data.get("snapshot_id")
    file_path = data.get("file_path")
    content = data.get("content")
    created_at = data.get("created_at")
    snapshot = ProjectVersionSnapshot.query.filter_by(id=snapshot_id).first()
    if not snapshot:
        return error_response("任务不存在！", 404, {})
    code_file = CodeFile.query.filter_by(project_id=project_id, file_path=file_path).first()
    if not code_file:
        return error_response("文件不存在！", 404, {})
    # TODO 代码变更判断line_added_begin, line_added_end
    #  line_removed_begin, line_removed_end，以及change_description变更描述
    #  需要进一步完善
    from api.common.utils.help_functions import deterministic_hash
    from uuid import uuid4
    current_content_hash = deterministic_hash(content)
    exist_file_version = (CodeFileVersion.query.filter_by(code_file_id=code_file.id).
                          order_by(CodeFileVersion.version_number.desc()).first())
    if exist_file_version:
        if exist_file_version.content_hash == current_content_hash:     # 文件内容没变
            code_file_version_snapshot_association = CodeFileVersionSnapshotAssociation(
                code_file_version_id=exist_file_version.id,
                project_version_snapshot_id=snapshot_id
            )
            db.session.add(code_file_version_snapshot_association)
            db.session.commit()
            return success_response({}, "文件内容未改变，请勿重复上传！", 201)
        version_number = exist_file_version.version_number + 1      # 文件内容发生改变
        code_file_version = CodeFileVersion(
            id=uuid4(),
            code_file_id=code_file.id,
            content=content,
            content_hash=current_content_hash,
            updated_at=created_at,
            updated_by=user_id,
            version_number=version_number
        )
    else:
        code_file_version = CodeFileVersion(
            id=uuid4(),
            code_file_id=code_file.id,
            content=content,
            content_hash=current_content_hash,
            updated_at=created_at,
            updated_by=user_id
        )
    db.session.add(code_file_version)
    code_file_version_snapshot_association = CodeFileVersionSnapshotAssociation(
        code_file_version_id=code_file_version.id,
        project_version_snapshot_id=snapshot_id
    )
    db.session.add(code_file_version_snapshot_association)
    db.session.commit()
    return success_response(
        data={
            "snapshot_id": str(snapshot_id),
            "file_path": file_path,
            "updated_at": created_at,
        },
        message="上传文件成功！",
        status_code=201
    )


@service_bp.route('/projects/<project_id>/versions', methods=['DELETE'])
@jwt_required()
def delete_project_version_snapshot(project_id):
    user_id = get_jwt_identity()
    if not ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first():
        return error_response("用户不是项目成员，请联系管理员添加成员！", 403, {})
    data = request.get_json()
    snapshot_id = data.get("snapshot_id")
    snapshot = ProjectVersionSnapshot.query.filter_by(id=snapshot_id).first()
    if not snapshot:
        return error_response("当前版本快照不存在！", 404, {})
    associated_versions = snapshot.code_file_versions.all()
    db.session.delete(snapshot)     # 删除当前快照，然后级联删除中间表的记录
    db.session.flush()
    # 删除未被引用的CodeFileVersion记录
    for version in associated_versions:
        remaining_associations_count = CodeFileVersionSnapshotAssociation.query.filter_by(
            code_file_version_id=version.id
        ).count() + VersionTaskAssociation.query.filter_by(
            version_id=version.id
        ).count()
        if remaining_associations_count == 0:
            db.session.delete(version)
    db.session.commit()
    return success_response({}, "删除版本快照成功！", 200)


@service_bp.route('/projects/<project_id>/versions', methods=['GET'])
@jwt_required()
def get_project_version_snapshots(project_id):
    user_id = get_jwt_identity()
    if not ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first():
        return error_response("用户不是项目成员，请联系管理员添加成员！", 403, {})
    snapshots = []
    for snapshot in ProjectVersionSnapshot.query.filter_by(project_id=project_id).all():
        created_by = User.query.filter_by(id=snapshot.created_by).first().username
        snapshots.append({
            "snapshot_id": str(snapshot.id),
            "name": snapshot.name,
            "description": snapshot.description,
            "created_by": created_by,
            "created_at": snapshot.created_at.isoformat(),
        })
    return success_response(
        data=snapshots,
        message="获取版本快照列表成功！",
        status_code=200
    )


@service_bp.route('/projects/<project_id>/versions/<snapshot_id>', methods=['GET'])
@jwt_required()
def get_project_version_snapshot_detail(project_id, snapshot_id):
    user_id = get_jwt_identity()
    if not ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first():
        return error_response("用户不是项目成员，请联系管理员添加成员！", 403, {})
    snapshot = ProjectVersionSnapshot.query.filter_by(id=snapshot_id).first()
    if not snapshot:
        return error_response("当前版本快照不存在！", 404, {})
    code_file_list = []
    files_info = db.session.query(
        CodeFile,
        CodeFileVersion.id.label('version_id')
    ).select_from(ProjectVersionSnapshot).join(
        CodeFileVersionSnapshotAssociation,
        ProjectVersionSnapshot.id == CodeFileVersionSnapshotAssociation.project_version_snapshot_id
    ).join(
        CodeFileVersion,
        CodeFileVersion.id == CodeFileVersionSnapshotAssociation.code_file_version_id
    ).join(
        CodeFile,
        CodeFile.id == CodeFileVersion.code_file_id
    ).filter(
        ProjectVersionSnapshot.id == snapshot_id
    ).with_entities(
        CodeFile.id,
        CodeFile.file_path,
        CodeFile.file_size,
        CodeFileVersion.updated_by,
        CodeFileVersion.updated_at,
        CodeFileVersion.change_description,
        CodeFileVersion.id.label('version_id')
    ).all()
    for file_info in files_info:
        from api.common.utils.help_functions import format_file_size
        file_size = format_file_size(file_info.file_size)   # 字节单位转换一下
        code_file_list.append({
            "code_file_id": str(file_info.id),
            "file_path": file_info.file_path,
            "file_size": file_size,
            "code_file_version_id": str(file_info.version_id),
            "change_description": file_info.change_description,
            "updated_by": User.query.filter_by(id=file_info.updated_by).first().username,
            "updated_at": file_info.updated_at.isoformat(),
        })
    snapshot_detail = {
        "project_name": Project.query.filter_by(id=project_id).first().name,
        "snapshot_name": snapshot.name,
        "snapshot_description": snapshot.description,
        "created_by": User.query.filter_by(id=snapshot.created_by).first().username,
        "created_at": snapshot.created_at.isoformat(),
        "file_list_info": code_file_list,
    }
    return success_response(
        data=snapshot_detail,
        message="获取版本快照详情成功！",
        status_code=200
    )



