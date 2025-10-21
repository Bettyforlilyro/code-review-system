import streamlit as st

from ui.show_project import show_project_table
from ui.show_tasks import check_task_updates


def show_main_app():
    """
    显示主应用（已登录状态）
    1. 代码质量检查功能页签：一个代码文本输入框+一个文件上传输入框，用户必须在代码框中输入一段代码或者上传一个代码文件（如果是文件需要读取文本内容），然后点击提交并审查按钮，我们将数据提交给后端分析并获取分析结果
    2. 代码辅助工具功能页签：先仅仅做个页签即可，页面暂时空白我还没想好
    3. 测试用例生成功能页签：先仅仅做个页签即可，页面暂时空白我还没想好
    4. 项目知识库问答功能页签：先仅仅做个页签即可，页面暂时空白我还没想好
    5. 报告获取功能页签：是前4个功能得到后端响应结果之后才能点开这个页签，否则提示请等待分析结果不允许点开
    """

    st.title(f"欢迎，{st.session_state.user['username']}!")

    show_project_table()
    check_task_updates()


