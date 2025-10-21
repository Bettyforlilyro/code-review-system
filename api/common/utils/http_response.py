from flask import jsonify


def success_response(data=None, message="操作成功", status_code=200):
    """
    生成标准成功响应
    """
    return jsonify({
        "data": data or {},
        "message": message
    }), status_code

def error_response(message, status_code, data=None):
    """
    生成标准错误响应
    """
    return jsonify({
        "data": data or {},
        "message": message
    }), status_code