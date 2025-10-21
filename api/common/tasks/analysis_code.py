import time

from api.celery_app import celery_app


@celery_app.task(bind=True, name="api.common.tasks.analysis_code.analyze_code_task", queue="default")
def analyze_code_task(self, code, language):
    time.sleep(5)
    result = {
        "score": 99,
        "issues": [
            {
                "type": "bug",
                "description": code,
                "severity": "serious",
                "suggestion": "rollback"
            }
        ],
        "statistics": {
            "total_lines": 1000,
            "function_count": 5,
            "complexity": 15,
        }
    }
    return result
