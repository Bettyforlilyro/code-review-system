import time
from typing import Dict

import requests
import streamlit as st

from ui.global_def import *


def process_task_notifications():
    """处理来自子线程的任务通知"""
    with task_results_lock:
        if task_results:
            for task_id, result_data in list(task_results.items()):
                st.session_state.analysis_result = result_data
                st.session_state.task_notifications.append({
                    "task_id": task_id,
                    "message": f"任务 {task_id[:8]} 分析完成！",
                    "status": result_data.get("status")
                })
                # 从全局字典中移除已处理的任务
                del task_results[task_id]
                # 通知子线程终止
                with active_threads_lock:
                    if task_id in active_threads_events:
                        active_threads_events[task_id].set()
                        del active_threads_events[task_id]


def show_notifications_task_finish():
    """显示通知"""
    if st.session_state.task_notifications:
        for task_notification in st.session_state.task_notifications:
            if task_notification["status"] == "completed":
                st.toast(task_notification["message"], icon="✅")
            else:
                st.toast(task_notification["message"], icon="❌")
        st.session_state.task_notifications = []


def poll_task_status(task_id: str, headers: Dict[str, str], stop_event: threading.Event):
    """子线程-轮询任务状态的函数"""
    while not stop_event.is_set():
        try:
            response = requests.get(
                f"{BASE_URL}/service/tasks/{task_id}",
                headers=headers
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("status") in ["completed", "failed"]:
                    # 任务完成，将结果保存到全局变量中
                    with task_results_lock:
                        task_results[task_id] = result.get('result')
                        task_results[task_id]["status"] = result.get("status")
                    # 从待处理任务中移除
                    with pending_tasks_lock:
                        if task_id in pending_tasks:
                            del pending_tasks[task_id]
                    global should_rerun_flag, should_rerun_lock
                    # 通知主线程刷新界面状态
                    with should_rerun_lock:
                        should_rerun_flag = True
                    break
            # 等待一段时间再轮询
            if not stop_event.wait(5):
                continue
        except Exception as e:
            print(f"轮询任务状态时出错: {str(e)}")
            time.sleep(5)


@st.fragment(run_every=2)   # 每2秒执行一次
def check_task_updates():
    global should_rerun_flag, should_rerun_lock
    with should_rerun_lock:
        if should_rerun_flag:
            should_rerun_flag = False
            process_task_notifications()
            show_notifications_task_finish()
            time.sleep(1.5)     # 避免弹窗太快就重新运行绘制界面而消失
            st.rerun()