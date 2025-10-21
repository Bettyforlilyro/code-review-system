from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity

from api.common.utils.http_response import success_response, error_response
from api.models.model_project import Project, ProjectMember, db
from api.models.model_user import User
from api.services import bp as service_bp


@service_bp.route('/projects', methods=['POST'])
@jwt_required()
def create_project():
    data = request.get_json()
    owner_id = get_jwt_identity()
    project_name = data.get('name')
    description = data.get('description')
    programming_language = data.get('programming_language', 'python')
    local_path = data.get('root_path')
    current_project = Project(
        name=project_name,
        description=description,
        programming_language=programming_language,
        local_path=local_path,
        owner_id=owner_id
    )
    db.session.add(current_project)
    db.session.commit()
    import time
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    # 创建项目者自动成为项目owner
    project_owner = ProjectMember(
        project_id=current_project.id,
        user_id=owner_id,
        role="owner",
        joined_at=current_time
    )
    db.session.add(project_owner)
    db.session.commit()
    # 返回创建成功信息，前端此时应该跳转至项目详情页面
    data = {
        "project_id": str(current_project.id),
        "name": project_name,
        "description": description,
        "created_at": current_time
    }
    return success_response(data, "项目创建成功", 201)


@service_bp.route('/projects', methods=['GET'])
@jwt_required()
def get_project_list_of_current_user():
    # 优先显示owner是自己的项目
    user_id = get_jwt_identity()
    # 查询用户参与的所有项目，按照角色优先级排序，owner > architect > developer
    projects_with_roles = db.session.query(Project, ProjectMember.role).join(
        ProjectMember, Project.id == ProjectMember.project_id
    ).filter(
        ProjectMember.user_id == user_id
    ).order_by(
        db.case(
            (ProjectMember.role == 'owner', 1),
            (ProjectMember.role == 'architect', 2),
            else_=3
        )
    ).all()
    project_list = []
    for project, role in projects_with_roles:
        project_list.append({
            "project_id": str(project.id),
            "name": project.name,
            "description": project.description,
            "created_at": project.created_at.isoformat(),
            "role": role
        })
    return success_response(project_list, "项目列表获取成功", 200)


@service_bp.route('/projects/<project_id>', methods=['GET'])
@jwt_required()
def get_project_detail(project_id):
    user_id = get_jwt_identity()
    # 用户必须是项目成员
    if not ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first():
        return error_response("用户不是项目成员，请联系管理员添加成员！", 403, {})
    project = Project.query.filter_by(id=project_id).first()
    # TODO 项目详情不止包括项目基本信息，待完善
    #  还有各种比如项目成员、项目审查任务、项目文件树列表、项目整体分析图等信息
    data = {
        "project_id": str(project.id),
        "name": project.name,
        "description": project.description,
        "created_at": project.created_at.isoformat(),
        "local_path": project.local_path,
        "programming_language": project.programming_language
    }
    return success_response(data, "项目详情获取成功", 200)


@service_bp.route('/projects/<project_id>', methods=['PUT'])
@jwt_required()
def update_project_detail(project_id):
    user_id = get_jwt_identity()
    if not ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first():
        return error_response("用户不是项目成员，请联系管理员添加成员！", 403, {})
    data = request.get_json()
    # 暂时只支持修改name, description
    name = data.get('name')
    if name:
        Project.query.filter_by(id=project_id).update(
            {
                'name': name
            }
        )
    description = data.get('description')
    if description:
        Project.query.filter_by(id=project_id).update(
            {
                'description': description
            }
        )
    data = {
        "name": name,
        "description": description
    }
    return success_response(data, "项目详情更新成功", 200)


@service_bp.route('/projects/<project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    user_id = get_jwt_identity()
    user_member = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
    if not user_member or user_member.role != 'owner':
        return error_response("用户不是项目owner，无法删除项目！", 403, {})
    # 删除项目
    project = Project.query.filter_by(id=project_id).first()
    if project:
        db.session.delete(project)      # 级联删除所有项目关系
        db.session.commit()
    return success_response({}, "项目删除成功", 200)


@service_bp.route('/projects/<project_id>/members', methods=['GET'])
@jwt_required()
def get_project_members(project_id):
    user_id = get_jwt_identity()
    if not ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first():
        return error_response("用户不是项目成员，请联系管理员添加成员！", 403, {})
    # 依次显示owner, architect, developer
    member_list = ProjectMember.query.filter_by(project_id=project_id).order_by(
        db.case(
            (ProjectMember.role == 'owner', 1),
            (ProjectMember.role == 'architect', 2),
            else_=3
        )
    ).all()
    # 将ORM对象转换成字典列表
    members = []
    for member in member_list:
        user_id = member.user_id
        user = User.query.filter_by(id=user_id).first()
        members.append({
            "member_name": user.username,
            "member_email": user.email,
            "member_role": member.role,
            "member_joined_at": member.joined_at.isoformat()
        })
    return success_response(members, "项目成员列表获取成功", 200)


@service_bp.route('/projects/<project_id>/members', methods=['POST'])
@jwt_required()
def register_project_member(project_id):
    """给项目添加成员或者修改已有项目成员的权限"""
    user_id = get_jwt_identity()
    user = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
    if not user or (user.role != 'owner' and user.role != 'architect'):
        return error_response("用户不是项目owner或architect，无法添加项目成员！", 403, {})
    data = request.get_json()
    member_name = data.get('member_name')
    member_email = data.get('member_email')
    new_role = data.get('role')
    # 查询用户是否已注册
    member = User.query.filter_by(username=member_name, email=member_email).first()
    if not member:
        return error_response("该用户未注册，请先注册用户！", 400, {})
    # 如果用户已经加入了当前项目，则修改用户角色
    exist_member = ProjectMember.query.filter_by(project_id=project_id, user_id=member.id).first()
    if exist_member:
        ProjectMember.query.filter_by(project_id=project_id, user_id=member.id).update(
            {
                'role': new_role
            }
        )
        db.session.commit()
        data = {
            "member_name": member.username,
            "member_email": member.email,
            "member_role": new_role,
            "member_joined_at": exist_member.joined_at.isoformat()
        }
        return success_response(data, "项目成员角色修改成功", 200)
    else:   # 否则将用户添加到项目中
        project_member = ProjectMember(
            project_id=project_id,
            user_id=member.id,
            role=new_role
        )
        db.session.add(project_member)
        db.session.commit()
        data = {
            "member_name": member.username,
            "member_email": member.email,
            "member_role": new_role,
            "member_joined_at": project_member.joined_at.isoformat()
        }
        return success_response(data, "项目成员添加成功", 200)


@service_bp.route('/projects/<project_id>/members', methods=['DELETE'])
@jwt_required()
def remove_project_member(project_id):
    """从当前项目中直接移除项目成员"""
    user_id = get_jwt_identity()
    user = ProjectMember.query.filter_by(project_id=project_id, user_id=user_id).first()
    if not user or (user.role != 'owner' and user.role != 'architect'):
        return error_response("用户不是项目owner或architect，无法移除项目成员！", 403, {})
    data = request.get_json()
    member_name = data.get('member_name')
    member_email = data.get('member_email')
    member = User.query.filter_by(username=member_name, email=member_email).first()
    if not member:
        return error_response("该用户未注册，请先注册用户！", 400, {})
    project_member = ProjectMember.query.filter_by(project_id=project_id, user_id=member.id).first()
    if not project_member:
        return error_response("该用户不是项目成员，请勿重复移除！", 400, {})
    member_data = {
        "member_name": member_name,
        "member_email": member_email,
        "member_role": project_member.role,
        "member_joined_at": project_member.joined_at.isoformat()
    }
    db.session.delete(project_member)
    db.session.commit()
    return success_response(member_data, "项目成员移除成功", 200)
