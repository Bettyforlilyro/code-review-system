import logging
import json
import time
from flask import request, g

audit_logger = logging.getLogger('AUDIT')
audit_logger.setLevel(logging.INFO)
handler = logging.FileHandler('../logs/audit.log')
handler.setFormatter(logging.Formatter('%(message)s'))
audit_logger.addHandler(handler)


def init_audit_log(app):
    @app.before_request
    def before():
        g.start_time = time.time()

    @app.after_request
    def after(response):
        duration_ms = (time.time() - g.start_time) * 1000
        log_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "method": request.method,
            "path": request.path,
            "user": getattr(g, 'current_user', 'anonymous'),
            "role": getattr(g, 'role', 'developer'),
            "ip": request.remote_addr,
            "status": response.status_code,
            "duration_ms": round(duration_ms, 2)
        }
        audit_logger.info(json.dumps(log_data))
        return response
