from flask_jwt_extended import jwt_required
from sqlalchemy import select
from api.common.tasks.analysis_code import analyze_code_task
from api.services import bp as services_bp
from flask import request, jsonify
from api.gateway.auth import has_permission
import time
from api.models import db
from api.models.model_user import User


@services_bp.route('/analysis', methods=['POST'])
@jwt_required()
def analyze_code():
    data = request.get_json()
    code = data.get('code')
    language_type = data.get('language')
    task = analyze_code_task.delay(code, language_type)
    return jsonify(({
        'task_id': task.id,
        'message': 'analyze started...'
    })), 200


@services_bp.route('/healthcheck', methods=['GET'])
@jwt_required()
def healthcheck():
    try:
        status = {
            'status': 'healthy',
            'timestamp': time.time(),
            'version': '1.0.0',
            'services': {}
        }
        # db
        try:
            db.session.execute(select(User))
            status['services']['db'] = 'healthy'
        except Exception as e:
            status['services']['db'] = 'error' + str(e)
            status['status'] = 'degraded'
        # LLM
        try:
            from api.common.llm_client import llm_client
            llm_client.health_check()
            status['services']['llm'] = 'healthy'
        except Exception as e:
            status['services']['llm'] = 'error' + str(e)
            status['status'] = 'degrade'
        # chroma db
        try:
            from api.common.utils import vector_db
            vector_db.health_check()
            status['services']['vector_db'] = 'healthy'
        except Exception as e:
            status['services']['vector_db'] = 'error' + str(e)
            status['status'] = 'degrade'
    except Exception as e:
        return jsonify({
            'status': 'error' + str(e)
        }), 500
    return jsonify(status), 200
