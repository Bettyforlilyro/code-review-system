import streamlit as st
import requests
import os
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
import json
from typing import List, Dict, Any
import time

# 后端API基础URL
BASE_URL = "http://localhost:5000/api"


def main():
    st.set_page_config(page_title="文件上传工具", page_icon="📁", layout="wide")

    st.title("📁 本地文件扫描与上传工具")
    st.markdown("递归扫描本地文件夹并异步上传所有文件到后端处理")

    # 初始化session state
    if 'upload_tasks' not in st.session_state:
        st.session_state.upload_tasks = {}
    if 'scanning' not in st.session_state:
        st.session_state.scanning = False
    if 'uploading' not in st.session_state:
        st.session_state.uploading = False

    # 侧边栏配置
    with st.sidebar:
        st.header("配置")
        folder_path = st.text_input("文件夹路径", value="./test_files")
        file_extensions = st.text_input("文件扩展名（逗号分隔）", value=".txt,.py,.json,.md")
        max_file_size = st.number_input("最大文件大小 (MB)", min_value=1, value=10)
        chunk_size = st.number_input("分块大小 (KB)", min_value=10, value=512)

        col1, col2 = st.columns(2)
        with col1:
            scan_btn = st.button("🔍 扫描文件", use_container_width=True)
        with col2:
            upload_btn = st.button("🚀 开始上传", use_container_width=True,
                                   disabled=not st.session_state.upload_tasks)

    # 主内容区
    tab1, tab2, tab3 = st.tabs(["文件扫描", "上传管理", "系统状态"])

    with tab1:
        show_scan_tab(folder_path, file_extensions, max_file_size, scan_btn)

    with tab2:
        show_upload_tab(upload_btn, chunk_size)

    with tab3:
        show_status_tab()


def show_scan_tab(folder_path: str, file_extensions: str, max_file_size: int, scan_btn: bool):
    """显示文件扫描标签页"""
    st.header("文件扫描")

    if scan_btn:
        scan_files(folder_path, file_extensions, max_file_size)

    # 显示已扫描的文件
    if st.session_state.upload_tasks:
        st.subheader(f"已找到 {len(st.session_state.upload_tasks)} 个文件")

        # 文件统计
        total_size = sum(task['size'] for task in st.session_state.upload_tasks.values())
        st.info(f"总大小: {total_size / 1024 / 1024:.2f} MB")

        # 文件列表
        with st.expander("查看文件列表", expanded=False):
            for file_path, task in list(st.session_state.upload_tasks.items())[:50]:  # 只显示前50个
                st.write(f"📄 {file_path} ({task['size'] / 1024:.1f} KB)")

            if len(st.session_state.upload_tasks) > 50:
                st.write(f"... 还有 {len(st.session_state.upload_tasks) - 50} 个文件")


def scan_files(folder_path: str, file_extensions: str, max_file_size: int):
    """扫描文件夹中的文件"""
    if not os.path.exists(folder_path):
        st.error(f"文件夹不存在: {folder_path}")
        return

    st.session_state.scanning = True
    st.session_state.upload_tasks = {}

    # 解析文件扩展名
    extensions = [ext.strip().lower() for ext in file_extensions.split(',')]
    max_size_bytes = max_file_size * 1024 * 1024

    # 创建进度条
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # 递归扫描文件
        file_count = 0
        scanned_files = []

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)

                # 检查文件扩展名
                file_ext = os.path.splitext(file)[1].lower()
                if extensions and file_ext not in extensions:
                    continue

                # 检查文件大小
                file_size = os.path.getsize(file_path)
                if file_size > max_size_bytes:
                    st.warning(f"跳过大文件: {file_path} ({file_size / 1024 / 1024:.1f} MB)")
                    continue

                scanned_files.append((file_path, file_size))

        # 更新任务列表
        total_files = len(scanned_files)
        for i, (file_path, file_size) in enumerate(scanned_files):
            st.session_state.upload_tasks[file_path] = {
                'path': file_path,
                'size': file_size,
                'status': 'pending',  # pending, uploading, completed, failed
                'progress': 0,
                'uploaded_bytes': 0,
                'error': None
            }

            # 更新进度
            progress = (i + 1) / total_files
            progress_bar.progress(progress)
            status_text.text(f"扫描进度: {i + 1}/{total_files} 文件")

        status_text.text(f"扫描完成! 找到 {total_files} 个文件")

    except Exception as e:
        st.error(f"扫描文件时出错: {str(e)}")
    finally:
        st.session_state.scanning = False


def show_upload_tab(upload_btn: bool, chunk_size: int):
    """显示上传管理标签页"""
    st.header("文件上传管理")

    if not st.session_state.upload_tasks:
        st.info("请先扫描文件")
        return

    # 上传控制
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总文件数", len(st.session_state.upload_tasks))
    with col2:
        completed = sum(1 for t in st.session_state.upload_tasks.values() if t['status'] == 'completed')
        st.metric("已完成", completed)
    with col3:
        failed = sum(1 for t in st.session_state.upload_tasks.values() if t['status'] == 'failed')
        st.metric("失败", failed)

    # 开始上传按钮
    if upload_btn and not st.session_state.uploading:
        asyncio.run(async_upload_files(chunk_size * 1024))  # 转换为字节

    # 上传进度
    if st.session_state.upload_tasks:
        show_upload_progress()


def show_upload_progress():
    """显示上传进度"""
    st.subheader("上传进度")

    # 总体进度
    total_files = len(st.session_state.upload_tasks)
    completed_files = sum(1 for t in st.session_state.upload_tasks.values() if t['status'] == 'completed')
    uploading_files = sum(1 for t in st.session_state.upload_tasks.values() if t['status'] == 'uploading')

    overall_progress = completed_files / total_files if total_files > 0 else 0
    st.progress(overall_progress)
    st.write(f"总体进度: {completed_files}/{total_files} 文件 ({overall_progress * 100:.1f}%)")

    # 当前上传的文件
    uploading_tasks = [t for t in st.session_state.upload_tasks.values() if t['status'] == 'uploading']
    if uploading_tasks:
        current_file = uploading_tasks[0]
        st.write(f"**当前上传:** {os.path.basename(current_file['path'])}")
        st.progress(current_file['progress'])
        st.write(f"文件进度: {current_file['uploaded_bytes'] / 1024:.1f} KB / {current_file['size'] / 1024:.1f} KB")

    # 详细文件列表
    with st.expander("详细上传状态", expanded=True):
        # 按状态分组显示
        status_groups = {}
        for task in st.session_state.upload_tasks.values():
            status = task['status']
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(task)

        for status, tasks in status_groups.items():
            status_icon = {
                'pending': '⏳',
                'uploading': '🔄',
                'completed': '✅',
                'failed': '❌'
            }.get(status, '❓')

            with st.expander(f"{status_icon} {status.capital()} ({len(tasks)} 文件)"):
                for task in tasks[:20]:  # 限制显示数量
                    file_name = os.path.basename(task['path'])
                    if status == 'uploading':
                        st.write(f"{file_name} - {task['progress'] * 100:.1f}%")
                    elif status == 'failed':
                        st.write(f"{file_name} - {task['error']}")
                    else:
                        st.write(file_name)

                if len(tasks) > 20:
                    st.write(f"... 还有 {len(tasks) - 20} 个文件")


async def async_upload_files(chunk_size: int):
    """异步上传文件"""
    st.session_state.uploading = True

    # 创建异步任务
    tasks = []
    semaphore = asyncio.Semaphore(3)  # 限制并发数

    for file_task in st.session_state.upload_tasks.values():
        if file_task['status'] == 'pending':
            task = asyncio.create_task(
                upload_file_with_semaphore(file_task, chunk_size, semaphore)
            )
            tasks.append(task)

    # 等待所有任务完成
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

    st.session_state.uploading = False
    st.rerun()


async def upload_file_with_semaphore(file_task: dict, chunk_size: int, semaphore: asyncio.Semaphore):
    """使用信号量控制并发上传"""
    async with semaphore:
        await upload_single_file(file_task, chunk_size)


async def upload_single_file(file_task: dict, chunk_size: int):
    """上传单个文件（支持分块）"""
    file_path = file_task['path']

    try:
        # 更新状态
        file_task['status'] = 'uploading'

        # 读取并上传文件
        async with aiofiles.open(file_path, 'rb') as file:
            file_content = await file.read()

        # 准备上传数据
        file_name = os.path.basename(file_path)
        relative_path = os.path.relpath(file_path, os.path.dirname(file_task.get('base_path', '')))

        upload_data = {
            'file_name': file_name,
            'file_path': relative_path,
            'file_size': len(file_content),
            'file_content': file_content.hex(),  # 将二进制转换为十六进制字符串传输
            'file_type': 'text' if is_text_file(file_path) else 'binary'
        }

        # 上传到后端
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {st.session_state.get('token', '')}",
                "Content-Type": "application/json"
            }

            async with session.post(
                    f"{BASE_URL}/files/upload",
                    json=upload_data,
                    headers=headers
            ) as response:

                if response.status == 200:
                    file_task['status'] = 'completed'
                    file_task['progress'] = 1.0
                    file_task['uploaded_bytes'] = file_task['size']
                else:
                    error_text = await response.text()
                    file_task['status'] = 'failed'
                    file_task['error'] = f"HTTP {response.status}: {error_text}"

    except Exception as e:
        file_task['status'] = 'failed'
        file_task['error'] = str(e)


def is_text_file(file_path: str) -> bool:
    """判断是否为文本文件"""
    text_extensions = {'.txt', '.py', '.json', '.md', '.xml', '.html', '.css', '.js', '.csv'}
    return os.path.splitext(file_path)[1].lower() in text_extensions


def show_status_tab():
    """显示系统状态标签页"""
    st.header("系统状态")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("内存使用")
        # 这里可以添加内存监控逻辑
        st.info("内存监控功能需要安装 psutil 库")

        st.subheader("网络状态")
        # 测试后端连接
        if st.button("测试后端连接"):
            try:
                response = requests.get(f"{BASE_URL}/health")
                if response.status_code == 200:
                    st.success("✅ 后端连接正常")
                else:
                    st.error(f"❌ 后端连接异常: {response.status_code}")
            except Exception as e:
                st.error(f"❌ 无法连接到后端: {str(e)}")

    with col2:
        st.subheader("任务统计")
        if st.session_state.upload_tasks:
            status_counts = {}
            for task in st.session_state.upload_tasks.values():
                status = task['status']
                status_counts[status] = status_counts.get(status, 0) + 1

            for status, count in status_counts.items():
                st.write(f"{status}: {count}")
        else:
            st.write("暂无任务")


if __name__ == "__main__":
    main()