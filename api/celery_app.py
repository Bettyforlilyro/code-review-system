import os

from celery import Celery

from api.common.config.celery_config import celery_config
import api.common.tasks     # 导入所有任务，必须保留；同时需要在tasks\__init__.py中导入所有.py文件

# 全局celery实例
celery_app = Celery("Code-review")
celery_app.conf.update(celery_config)


if __name__ == "__main__":
    # 可通过环境变量或命令行指定队列
    queues = os.getenv("CELERY_QUEUES", "default,celery")
    argv = [
        "worker",
        "--loglevel=INFO",
        f"--queues={queues}",
        "--concurrency=4",  # 根据 CPU 核心数调整
        "--pool=threads",   # 或 "prefork"（默认），根据任务 I/O 密集型选择
    ]
    celery_app.start(argv)