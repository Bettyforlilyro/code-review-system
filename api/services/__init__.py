from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from api.gateway.auth import has_permission

bp = Blueprint('service_api', __name__, url_prefix='/api/v1')

# 需要显示导入所有服务，如果bp写在上面这里必须导入
from api.services.code_review_test import *
from api.services.code_projects.projects_manage_v1 import *
from api.services.code_projects.code_file_manage_v1 import *
from api.services.code_review.code_review_manage_v1 import *


@bp.route('/tasks/<task_id>', methods=['GET'])
@jwt_required()
def get_task_status(task_id):
    from celery.result import AsyncResult
    from api.celery_app import celery_app
    result = AsyncResult(task_id, app=celery_app)
    if result.ready():
        if result.successful():
            return jsonify({
                'task_id': task_id,
                'status': "completed",
                'result': result.result
            })
        else:
            return jsonify({
                'task_id': task_id,
                'status': "failed",
                'result': str(result.result)
            })
    else:
        return jsonify({
            'task_id': task_id,
            'status': "pending"
        })

