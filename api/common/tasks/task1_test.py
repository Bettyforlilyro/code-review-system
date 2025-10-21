import time

from api.celery_app import celery_app


@celery_app.task(bind=True, name="app.common.tasks.task1.add", queue="default")
def add(self, x: int, y: int) -> int:
    """一个简单的加法任务"""
    print(f"Adding {x} + {y}")
    return x + y


@celery_app.task(bind=True, name="app.common.tasks.task1.send_email", queue="default")
def send_email(self, to: str, subject: str) -> str:
    """模拟发送邮件（耗时操作）"""
    print(f"Sending email to {to}: {subject}")
    time.sleep(3)  # 模拟网络延迟
    return f"Email sent to {to}"

