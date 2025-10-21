from pathlib import Path
from typing import Union
import pandas as pd
import streamlit as st
import time
from ui.utils.ui_test_utils import build_directory_tree_recursive, get_project_files, add_node_to_directory_tree, is_text_file, \
    delete_tree_node_with_path


class HomePage:
    def __init__(self, username: str, project_name: str):
        self.username = username
        self.project_name = project_name
        self.project_dir = Path(st.session_state.selected_project["path"])

    def show_home(self):
        """显示项目主页"""
        st.title(f"🏠 项目主页 - {self.project_name}")
        # 在侧边栏显示目录树
        self._show_directory_tree()

        # 项目概览
        self._show_project_overview()

        # 文件管理
        selected_node = st.session_state.get("selected_node")
        if selected_node:
            # 如果是目录，中间显示目录下的所有文件统计信息，文件上传器，同时可以新建子文件夹以及文本文件到当前目录
            if selected_node["type"] == "directory":
                self._show_directory_manager()
                # 当前文件夹下的文件统计
                self._show_project_stats()
            # 如果是文件，中间显示文件内容（仅文本文件，二进制文件提示不支持显示），文本编辑框，同时可以保存文件
            elif selected_node["type"] == "file":
                self._show_file_manager()
            else:
                st.warning("无效的节点类型")

    def _show_directory_tree(self):
        """在侧边栏显示目录树"""
        st.sidebar.subheader("📁 目录结构")

        # 获取或初始化目录树
        tree_key = f"tree_{self.username}_{self.project_name}"
        if tree_key not in st.session_state:
            st.session_state[tree_key] = build_directory_tree_recursive(self.project_dir)
            st.session_state["selected_node"] = st.session_state[tree_key]  # 最开始选中根结点

        # 渲染目录树
        self._render_tree_component(st.session_state[tree_key])

        # 添加"返回项目根目录"按钮
        if st.sidebar.button("🏠 返回项目根目录"):
            if "selected_node" in st.session_state:
                st.session_state["selected_node"] = st.session_state[tree_key]

    def _render_tree_component(self, node: dict, level: int = 0):
        """渲染树形组件"""
        if node["type"] == "directory":
            # 文件夹节点 - 单行布局
            cols = st.sidebar.columns([2] * level + [5, 18])
            # 空白占位
            for i in range(level):
                with cols[i]:
                    st.write(" ")
            with cols[-2]:
                # 展开/折叠图标
                icon = "📂" if not node.get("expanded", False) else "📁"
                if st.button(
                        icon,
                        key=f"toggle_{node['path']}",
                        use_container_width=True
                ):
                    node["expanded"] = not node.get("expanded", False)
                    st.rerun()

            with cols[-1]:
                # 文件夹名称（可点击选择）
                display_name = f"{node['name']}"
                if st.button(
                        display_name,
                        key=f"select_{node['path']}",
                        use_container_width=True
                ):
                    st.session_state["selected_node"] = node

            # 递归渲染子节点（如果展开）
            if node.get("expanded", False):
                for child in node["children"]:
                    self._render_tree_component(child, level + 1)

        else:
            # 文件夹节点 - 单行布局
            cols = st.sidebar.columns([2] * level + [23])
            # 空白占位
            for i in range(level):
                with cols[i]:
                    st.write(" ")
            with cols[-1]:
                # 文件节点
                if st.button(f"📄 {node['name']}", key=f"select_file_{node['path']}", width='stretch'):
                    st.session_state["selected_node"] = node

    def _show_project_overview(self):
        """显示项目整体概览"""
        col1, col2, col3 = st.columns(3)

        files = get_project_files(st.session_state.selected_project["path"])
        total_size = sum(f["size"] for f in files) / 1024  # KB

        with col1:
            st.metric("文件数量", len(files))
        with col2:
            st.metric("总大小", f"{total_size:.1f} KB")
        with col3:
            st.metric("项目状态", "活跃")

    def _show_directory_manager(self):
        """显示目录管理器"""
        st.subheader(f"📂 当前目录 {st.session_state.selected_node['path']}")
        col1, col2 = st.columns(2)
        tree_key = f"tree_{self.username}_{self.project_name}"
        with col1:
            with st.form("new_folder_form"):
                folder_name = st.text_input("新建文件夹", key="new_folder_name")
                submit_folder = st.form_submit_button("新建文件夹")
                if submit_folder:
                    if folder_name:
                        new_folder_path = Path(st.session_state.selected_node["path"]) / folder_name
                        try:
                            new_folder_path.mkdir(parents=True)
                            st.success(f"成功创建文件夹 '{folder_name}'")
                            add_node_to_directory_tree(
                                node=st.session_state[tree_key],
                                path=st.session_state.selected_node["path"],
                                name=folder_name,
                                is_file=False
                            )
                            time.sleep(1.5)     # 避免太快刷新页面
                            st.rerun()
                        except FileExistsError:
                            st.warning(f"文件夹 '{folder_name}' 已存在")
                    else:
                        st.warning("请输入文件夹名称")
        with col2:
            with st.form("new_file_form"):
                file_name = st.text_input("新建文件", key="new_file_name")
                submit_file = st.form_submit_button("新建")
                if submit_file:
                    if file_name:
                        new_file_path = Path(st.session_state.selected_node["path"]) / file_name
                        try:
                            if new_file_path.exists():
                                raise FileExistsError
                            new_file_path.touch()
                            st.success(f"成功创建文件 '{file_name}'")
                            add_node_to_directory_tree(
                                node=st.session_state[tree_key],
                                path=st.session_state.selected_node["path"],
                                name=file_name,
                                is_file=True
                            )
                            time.sleep(1.5)     # 避免太快刷新页面
                            st.rerun()
                        except FileExistsError:
                            st.warning(f"文件 '{file_name}' 已存在")
                    else:
                        st.warning("请输入文件名称")
        if st.button("删除当前文件夹"):
            if st.session_state["selected_node"]["path"] == st.session_state.selected_project["path"]:
                st.warning("当前文件夹是项目根文件夹，如果要删除请从左侧直接删除项目")
            else:
                self._delete_file(st.session_state.selected_node["path"])

        # 文件上传器
        uploader_key = f"uploader_{st.session_state.selected_node['path']}"  # 不同子目录的key应该不同
        uploaded_file = st.file_uploader(
            "上传文件到当前文件夹",
            type=None,  # 允许所有类型
            key=uploader_key
        )
        if ((uploaded_file is not None) and
                (st.session_state.get("last_uploaded_file") != (uploader_key + uploaded_file.name))):
            # 条件满足进来之后都会执行st.rerun()
            file_path = Path(st.session_state.selected_node["path"]) / uploaded_file.name
            # 检查文件是否已存在
            if file_path.exists():
                st.warning(f"文件 '{uploaded_file.name}' 已存在，是否覆盖？")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("覆盖", key="overwrite"):
                        self._save_uploaded_file(uploaded_file, file_path, (uploader_key + uploaded_file.name))
                with col2:
                    if st.button("取消", key="cancel"):
                        # 标记为已处理但取消上传
                        st.session_state["last_uploaded_file"] = (uploader_key + uploaded_file.name)
                        st.rerun()
            else:
                add_node_to_directory_tree(
                    node=st.session_state[tree_key],
                    path=st.session_state.selected_node["path"],
                    name=uploaded_file.name,
                    is_file=True
                )
                self._save_uploaded_file(uploaded_file, file_path, (uploader_key + uploaded_file.name))

        files = get_project_files(Path(st.session_state.selected_node["path"]))
        if not files:
            st.info("文件夹为空，请上传或创建文件")
        # 显示文件列表
        if files:
            st.subheader("文件列表")
            file_data = []
            for file_info in files:
                file_data.append({
                    "文件名": file_info["name"],
                    "路径": file_info["relative_path"],
                    "大小 (KB)": f"{file_info['size'] / 1024:.1f}"
                })

            df = pd.DataFrame(file_data)
            st.dataframe(df, width='content')

    def _show_file_manager(self):
        """显示文件管理器"""
        st.subheader("📂 文件管理")
        # 直接显示文件内容（仅支持文本文件，二进制文件提示不支持预览）
        is_text = is_text_file(Path(st.session_state.selected_node["path"]))
        if is_text:
            with open(Path(st.session_state.selected_node["path"]), "r", encoding="utf-8") as f:
                file_content = f.read()
            edited_content = st.text_area("文件内容", value=file_content, height=500)
        else:
            st.warning("不支持预览此文件")
            edited_content = None
        col1, col2 = st.columns(2)
        with col1:
            if is_text:
                if st.button("保存文件"):
                    if edited_content and edited_content != file_content:
                        try:
                            with open(Path(st.session_state.selected_node["path"]), "w", encoding="utf-8") as f:
                                f.write(edited_content)
                            st.success("文件保存成功")
                            st.rerun()
                        except Exception as e:
                            st.error(f"文件保存失败: {str(e)}")
                    else:
                        st.warning("没有内容被修改")
        with col2:
            if st.button("删除文件"):
                self._delete_file(st.session_state.selected_node["path"])

    def _save_uploaded_file(self, uploaded_file, file_path, uploader_key):
        """保存上传的文件并处理状态"""
        try:
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"文件 '{uploaded_file.name}' 上传成功")
            # 标记这个上传器已处理
            st.session_state["last_uploaded_file"] = uploader_key
            st.rerun()
        except Exception as e:
            st.error(f"文件上传失败: {str(e)}")

    def _delete_file(self, file_path: Union[str, Path]):
        """删除文件或文件夹，file_path应该是从项目根路径开始的完整路径"""
        if isinstance(file_path, str):
            file_path = Path(file_path)
        if file_path.exists():
            tree_key = f"tree_{self.username}_{self.project_name}"
            if file_path.is_file():
                file_path.unlink()
                st.success(f"文件 '{file_path.name}' 删除成功")
            elif file_path.is_dir():
                import shutil
                shutil.rmtree(file_path)
                st.success(f"文件夹 '{file_path.name}' 及其内容删除成功")
            delete_tree_node_with_path(st.session_state[tree_key], str(file_path))
            st.session_state.selected_node = None
            time.sleep(0.8)     # 防止页面刷新太快
            st.rerun()
        else:
            st.error("文件或文件夹不存在")

    def _show_project_stats(self):
        """显示当前文件夹中的文件统计信息"""
        st.subheader("📊 文件统计")

        files = get_project_files(Path(st.session_state.selected_node["path"]))
        if files:
            # 按文件类型统计
            file_extensions = {}
            for file_info in files:
                ext = Path(file_info["name"]).suffix.lower()
                file_extensions[ext] = file_extensions.get(ext, 0) + 1

            if file_extensions:
                st.write("文件类型分布:")
                for ext, count in file_extensions.items():
                    st.write(f"- {ext if ext else '无扩展名'}: {count} 个文件")
        else:
            st.info("暂无统计信息")