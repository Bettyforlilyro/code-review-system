import streamlit as st
from ui.global_def import *
import requests


def show_auth_page():
    """显示认证页面（登录/注册）"""
    tab1, tab2 = st.tabs(["登录", "注册"])

    with tab1:
        show_login_form()

    with tab2:
        show_register_form()


def show_login_form():
    """显示登录表单"""
    st.header("用户登录")

    with st.form("login_form"):
        username = st.text_input("用户名")
        password = st.text_input("密码", type="password")
        submit = st.form_submit_button("登录")

        if submit:
            if not username or not password:
                st.error("请填写用户名和密码")
                return

            try:
                response = requests.post(
                    f"{BASE_URL}/auth/login",
                    json={"username": username, "password": password}
                )

                if response.status_code == 200:
                    data = response.json()
                    st.session_state.token = data["access_token"]
                    st.session_state.user = data["user"]
                    st.success("登录成功！")
                    st.rerun()
                else:
                    error_msg = response.json().get("error", "登录失败")
                    st.error(f"登录失败: {error_msg}")

            except Exception as e:
                st.error(f"无法连接到服务器: {str(e)}")


def show_register_form():
    """显示注册表单"""
    st.header("用户注册")

    with st.form("register_form"):
        username = st.text_input("用户名")
        email = st.text_input("邮箱")
        password = st.text_input("密码", type="password")
        confirm_password = st.text_input("确认密码", type="password")
        submit = st.form_submit_button("注册")

        if submit:
            if not username or not email or not password:
                st.error("请填写所有必填字段")
                return

            if password != confirm_password:
                st.error("两次输入的密码不一致")
                return

            if len(password) < 6:
                st.error("密码长度至少6位")
                return

            try:
                response = requests.post(
                    f"{BASE_URL}/auth/register",
                    json={
                        "username": username,
                        "email": email,
                        "password": password
                    }
                )

                if response.status_code == 201:
                    data = response.json()
                    st.session_state.token = data["access_token"]
                    st.session_state.user = data["user"]
                    st.success("注册成功！")
                    st.rerun()
                else:
                    error_msg = response.json().get("error", "注册失败")
                    st.error(f"注册失败: {error_msg}")

            except Exception as e:
                st.error(f"无法连接到服务器: {str(e)}")

