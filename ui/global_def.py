import threading

# 全局变量用于线程间通信
task_results = {}   # 保存已经有结果的任务
task_results_lock = threading.Lock()
pending_tasks = {}  # 保存正在处理的任务
pending_tasks_lock = threading.Lock()
should_rerun_flag = False   # 是否应该刷新界面
should_rerun_lock = threading.Lock()
# 管理后台线程，避免不必要的资源浪费
active_threads_lock = threading.Lock()
active_threads_events = {}

# 后端API基础URL
BASE_URL = "http://localhost:5000/api/v1"




