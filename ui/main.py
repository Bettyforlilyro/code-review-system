import time

import streamlit as st

from ui.global_def import *
from ui.show_auth import show_auth_page
from ui.show_home import show_main_app

st.set_page_config(
    page_title="Streamlit-Flask Code-Review App",
    page_icon="📚",
    initial_sidebar_state="expanded"
)


def init_session_state():
    # 初始化session state
    if 'token' not in st.session_state:
        st.session_state.token = None
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'task_notifications' not in st.session_state:
        st.session_state.task_notifications = []
    if 'current_projects' not in st.session_state:
        st.session_state.current_projects = {}
    if 'selected_project' not in st.session_state:
        st.session_state.selected_project = None
    # 清理所有全局状态
    with pending_tasks_lock:
        pending_tasks.clear()
    with task_results_lock:
        task_results.clear()
    # 停止所有后台线程
    with active_threads_lock:
        for task_id, thread_event in active_threads_events.items():
            thread_event.set()
        active_threads_events.clear()
    time.sleep(0.1)     # 等待一小会儿让线程有机会清理
    st.session_state.pending_tasks = {}
    st.session_state.task_notifications = None


def main():
    init_session_state()
    # 根据登录状态显示不同内容
    if st.session_state.token is None:
        show_auth_page()
    else:
        show_main_app()


if __name__ == '__main__':
    main()
