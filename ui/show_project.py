import time
from pathlib import Path

import requests
import streamlit as st

from global_def import *
from ui.home_page_manager import HomePage
from ui.show_tasks import poll_task_status
from ui.utils.ui_test_utils import get_user_projects_dir, _do_update_directory_expansion, build_directory_tree_recursive
import ui.api_test_fast as api_test_fast


def create_project(project_name: str) -> bool:
    """创建新项目"""
    # 检查项目名是否已存在，已存在则返回False不允许创建重名
    if st.session_state.current_projects.get(project_name):
        return False

    # 创建项目目录
    project_dir = get_user_projects_dir(st.session_state.user['username']) / project_name
    project_dir.mkdir(exist_ok=True)

    # 添加到项目列表
    new_project = {
        "name": project_name,
        "owner": st.session_state.user['username'],
        "path": str(project_dir),
        "created_at": st.session_state.get("current_time", time.strftime("%Y-%m-%d %H:%M:%S"))
    }
    st.session_state.current_projects[project_name] = new_project
    return True


def delete_project(project_name: str) -> bool:
    """删除项目"""
    projects = st.session_state.current_projects
    to_delete_project = projects.get(project_name, None)
    if not to_delete_project:
        return False
    # 校验只有owner才能删除项目
    if to_delete_project["owner"] != st.session_state.user['username']:
        return False

    # 删除项目目录
    project_dir = Path(to_delete_project["path"])
    if project_dir.exists():
        import shutil
        shutil.rmtree(project_dir)
    del st.session_state.current_projects[project_name]
    return True


def update_directory_expansion(path: str, expanded: bool):
    """更新目录展开状态"""
    tree_key = f"tree_{st.session_state.user['username']}_{st.session_state.selected_project['name']}"
    if tree_key in st.session_state:
        _do_update_directory_expansion(st.session_state[tree_key], path, expanded)


def show_project_sidebar():
    """在侧边栏显示项目管理界面"""
    st.sidebar.title("📁 项目管理")

    # 项目创建表单
    with (st.sidebar.expander("创建新项目", expanded=False)):
        with st.form("create_project_form"):
            new_project_name = st.text_input("项目名称")
            create_btn = st.form_submit_button("创建项目")
            if create_btn and new_project_name:
                success = create_project(new_project_name)
                if success:
                    # 切换到当前项目
                    current_project = st.session_state.current_projects[new_project_name]
                    # 切换项目清空可能已有的目录树缓存
                    if st.session_state.get("selected_project"):
                        tree_key = f"tree_{st.session_state.user['username']}_{st.session_state.selected_project['name']}"
                        if tree_key in st.session_state:
                            del st.session_state[tree_key]
                    if (not st.session_state.get("selected_project") or
                            (st.session_state.get("selected_project") != current_project)
                    ):
                        st.session_state.selected_project = current_project
                        tree_key = f"tree_{st.session_state.user['username']}_{new_project_name}"
                        if tree_key not in st.session_state:
                            st.session_state[tree_key] = build_directory_tree_recursive(current_project["path"])
                            st.session_state["selected_node"] = st.session_state[tree_key]  # 最开始选中根结点
                        st.session_state["is_created_lastly"] = True
                    st.rerun()
                else:
                    st.warning("项目已存在，请勿重复创建")

    # 项目列表
    if ('current_projects' not in st.session_state) or not st.session_state.current_projects:
        st.session_state.current_projects = read_exists_projects(st.session_state.user['username'])
    projects = st.session_state.current_projects
    if not projects:
        st.sidebar.info("暂无项目，请先创建项目")
        return None

    st.sidebar.subheader("我的项目")
    # 项目选择
    project_names = []
    for _, proj in projects.items():
        if proj["owner"] == st.session_state.user['username']:
            project_names.append(proj["name"])
    selected_project = st.sidebar.selectbox(
        "选择项目",
        options=[""] + project_names,
        index=0,
        key="project_selector"
    )

    # 项目管理操作
    if selected_project:
        st.sidebar.info(f"当前项目: **{selected_project}**")
        col1, col2 = st.sidebar.columns(2)
        with (col1):
            if st.button("打开项目", key="open_project"):
                if (st.session_state.get("selected_project") and
                        selected_project != st.session_state.selected_project["name"]):
                    # 如果切换项目清空可能已有的目录树缓存和已选中的文件或文件夹结点
                    tree_key = f"tree_{st.session_state.user['username']}_{st.session_state.selected_project['name']}"
                    if tree_key in st.session_state:
                        del st.session_state[tree_key]
                    if "selected_node" in st.session_state:
                        del st.session_state["selected_node"]
                st.session_state.selected_project = projects[selected_project]
                st.session_state["is_created_lastly"] = False
                st.rerun()

        with col2:
            if st.button("删除项目", key="delete_project"):
                success = delete_project(selected_project)
                if success:
                    st.session_state.selected_project = None
                    del st.session_state["is_created_lastly"]
                    st.rerun()
    # 如果是最新创建的项目直接返回即可
    if st.session_state.get("is_created_lastly"):
        return st.session_state.selected_project["name"]
    return selected_project  # 否则返回下拉框切换的项目


def read_exists_projects(username: str) -> dict:
    """获取当前目录下该用户已有的项目"""
    projects_path = get_user_projects_dir(username)
    list_projects = {}

    for project_name in projects_path.iterdir():
        new_project = {
            "name": project_name.name,
            "owner": st.session_state.user['username'],
            "path": str(project_name),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(project_name.stat().st_ctime))
        }
        list_projects[project_name.name] = new_project
    return list_projects


def show_project_table():
    # 显示顶部导航栏
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.title("📚 项目级代码审查系统")
    with col3:
        if st.button("🚪 退出登录"):
            st.session_state.token = None
            st.rerun()

    show_project_sidebar()
    if not st.session_state.selected_project:
        # 没有选择项目时的提示
        st.info("👈 请在左侧选择或创建一个项目")
        st.markdown("""
        ### 欢迎使用项目级代码审查系统！

        您可以：
        - 📁 **创建新项目** - 在左侧边栏创建新的项目
        - 🔄 **选择现有项目** - 从项目列表中选择已有项目
        - 📊 **管理项目文件** - 在项目内上传、查看和管理文件

        **开始使用：** 请在左侧边栏创建或选择一个项目。
        """)
    else:
        # 显示项目主页
        home_page = HomePage(st.session_state.user["username"], st.session_state.selected_project['name'])
        home_page.show_home()

        # 创建子功能页签
        tabs = st.tabs(["代码质量检查", "代码辅助工具", "测试用例生成", "项目知识库问答", "报告获取", "功能测试"])
        headers = {
            "Authorization": f"Bearer {st.session_state.token}",
            "Content-Type": "application/json"
        }

        # 代码质量检查页签
        with tabs[0]:
            st.header("代码质量检查")

            # 选择语言类型下拉单选框
            language_options = ["Python", "JavaScript", "Java", "C++", "C", "Go", "HTML", "CSS"]
            selected_language = st.selectbox(
                "选择语言类型",
                options=language_options,
                index=0,
                key="language_selector"
            )

            code_input = st.text_area("请输入代码:", height=300, key="code_text")
            uploaded_file = st.file_uploader("或上传代码文件:", type=["py", "js", "java", "cpp", "c", "html", "css"],
                                             key="code_file")

            if st.button("提交并审查"):
                code_content = None

                # 检查是否有代码输入或文件上传
                if code_input.strip():
                    code_content = code_input
                elif uploaded_file is not None:
                    # 读取上传的文件内容
                    code_content = uploaded_file.read().decode("utf-8")
                else:
                    st.warning("请提供代码内容或上传代码文件")
                    return

                # 提交代码到后端进行分析
                try:
                    response = requests.post(
                        f"{BASE_URL}/service/analysis",
                        json={
                            "code": code_content,
                            "language": selected_language
                        },
                        headers=headers
                    )

                    if response.status_code == 200:
                        task_id = response.json().get('task_id')
                        if task_id:
                            # 保存任务信息
                            with pending_tasks_lock:
                                pending_tasks[task_id] = {
                                    "code": code_content,
                                    "language": selected_language,
                                    "submitted_at": time.time()
                                }
                            # 启动后台线程轮询任务状态
                            event = threading.Event()
                            poll_thread = threading.Thread(
                                target=poll_task_status,
                                args=(task_id, headers, event),
                                daemon=True
                            )
                            poll_thread.start()
                            # 跟踪活动子线程
                            with active_threads_lock:
                                active_threads_events[task_id] = event
                            st.success("代码分析任务已提交，请等待分析完成后到报告界面中查看分析报告。")
                    else:
                        error_msg = response.json().get("error", "分析失败")
                        st.error(f"分析失败: {error_msg}")

                except Exception as e:
                    st.error(f"无法连接到服务器: {str(e)}")

        # 代码辅助工具页签
        with tabs[1]:
            st.header("代码辅助工具")
            st.info("此功能正在开发中...")

        # 测试用例生成功能页签
        with tabs[2]:
            st.header("测试用例生成")
            st.info("此功能正在开发中...")

        # 项目知识库问答功能页签
        with tabs[3]:
            st.header("项目知识库问答")
            st.info("此功能正在开发中...")

        # 报告获取功能页签
        with tabs[4]:
            show_report()

        # API快速测试功能页签
        with tabs[5]:
            api_test_fast.debug()


def show_report():
    st.header("分析报告")
    if st.session_state.analysis_result is None:
        st.warning("请先在'代码质量检查'页签中提交代码进行分析")
    else:
        # 显示分析结果
        result = st.session_state.analysis_result

        # 显示总体评分
        if "score" in result:
            st.subheader(f"代码质量评分: {result['score']}/100")

        # 显示问题列表
        if "issues" in result and result["issues"]:
            st.subheader("发现的问题:")
            for i, issue in enumerate(result["issues"], 1):
                with st.expander(f"问题 {i}: {issue.get('type', '未知类型')}"):
                    st.write("**描述:**", issue.get("description", "无描述"))
                    st.write("**严重程度:**", issue.get("severity", "未知"))
                    st.write("**建议修复方案:**", issue.get("suggestion", "无建议"))
        elif "issues" in result:
            st.success("未发现问题，代码质量良好！")

        # 显示其他统计信息
        if "statistics" in result:
            st.subheader("代码统计信息:")
            stats = result["statistics"]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("总行数", stats.get("total_lines", 0))
            with col2:
                st.metric("函数数量", stats.get("function_count", 0))
            with col3:
                st.metric("复杂度", stats.get("complexity", "未知"))
