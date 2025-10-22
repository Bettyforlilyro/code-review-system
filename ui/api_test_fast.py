import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import streamlit as st
import requests
from ui.global_def import *
import json

from ui.utils.file_utils import scan_folder_for_file_metadata


def debug():
    st.header("调试功能")
    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json"
    }
    # project_manage_test(headers=headers)
    # project_file_test(headers=headers)
    project_review_task_manage_test(headers=headers)


def project_manage_test(headers):
    if st.button("创建测试项目"):
        try:
            project_json = {
                "name": "测试项目",
                "description": "这是一个测试项目",
                "root_path": "D:/test",
                "programming_language": "python"
            }
            response = requests.post(
                url=f"{BASE_URL}/projects",
                headers=headers,
                data=json.dumps(project_json)
            )
            if response.status_code == 201:
                st.success(response.json().get("message"))
                for k, v in response.json().get("data").items():
                    st.write(f"{k}: {v}")
            else:
                st.error("创建项目失败")
        except Exception as e:
            st.error(f"无法连接到服务器: {str(e)}")
    if st.button("查询我的项目"):
        try:
            response = requests.get(
                url=f"{BASE_URL}/projects",
                headers=headers
            )
            if response.status_code == 200:
                st.success(response.json().get("message"))
                for project in response.json().get("data"):
                    for k, v in project.items():
                        st.write(f"{k}: {v}")
            else:
                st.error("查询项目失败")
        except Exception as e:
            st.error(f"无法连接到服务器: {str(e)}")
    if st.button("查询项目详情"):
        try:
            project_id = '8c42cca1-e8b8-421e-b1ae-b46ccf8ef083'     # 测试临时数据，目前是从数据库后台直接复制的
            response = requests.get(
                url=f"{BASE_URL}/projects/{project_id}",
                headers=headers
            )
            if response.status_code == 200:
                st.success(response.json().get("message"))
                for k, v in response.json().get("data").items():
                    st.write(f"{k}: {v}")
            else:
                st.error(f"查询项目详情失败，失败原因：{response.json().get('message')}")
        except Exception as e:
            st.error(f"无法连接到服务器: {str(e)}")
    if st.button("删除项目"):
        try:
            project_id = '8c42cca1-e8b8-421e-b1ae-b46ccf8ef083'     # 测试临时数据，目前是从数据库后台直接复制的
            response = requests.delete(
                url=f"{BASE_URL}/projects/{project_id}",
                headers=headers
            )
            if response.status_code == 200:
                st.success(response.json().get("message"))
            else:
                st.error(f"删除项目失败，失败原因：{response.json().get('message')}")
        except Exception as e:
            st.error(f"无法连接到服务器: {str(e)}")
    if st.button("获取项目所有成员列表"):
        try:
            project_id = '91b2170a-bc29-4807-8a35-ff22c9f3455f'     # 测试临时数据，目前是从数据库后台直接复制的
            response = requests.get(
                url=f"{BASE_URL}/projects/{project_id}/members",
                headers=headers
            )
            if response.status_code == 200:
                st.success(response.json().get("message"))
                for member in response.json().get("data"):
                    for k, v in member.items():
                        st.write(f"{k}: {v}")
            else:
                st.error(f"获取项目所有成员列表失败，失败原因：{response.json().get('message')}")
        except Exception as e:
            st.error(f"无法连接到服务器: {str(e)}")
    if st.button("添加项目成员"):
        try:
            project_id = '91b2170a-bc29-4807-8a35-ff22c9f3455f'
            member_json = {
                "member_name": "xlr",
                "member_email": "aizy@111.com",
                "role": "architect"
            }
            response = requests.post(
                url=f"{BASE_URL}/projects/{project_id}/members",
                headers=headers,
                data=json.dumps(member_json)
            )
            if response.status_code == 200:
                st.success(response.json().get("message"))
                st.write("新用户信息：")
                for k, v in response.json().get("data").items():
                    st.write(f"{k}: {v}")
            else:
                st.error(f"添加项目成员失败，失败原因：{response.json().get('message')}")
        except Exception as e:
            st.error(f"无法连接到服务器: {str(e)}")
    if st.button("删除项目成员"):
        try:
            project_id = '91b2170a-bc29-4807-8a35-ff22c9f3455f'
            member_json = {
                "member_name": "xlr",
                "member_email": "aizy@111.com"
            }
            response = requests.delete(
                url=f"{BASE_URL}/projects/{project_id}/members",
                headers=headers,
                data=json.dumps(member_json)
            )
            if response.status_code == 200:
                st.success(response.json().get("message"))
                st.write("删除用户信息：")
                for k, v in response.json().get("data").items():
                    st.write(f"{k}: {v}")
            else:
                st.error(f"删除项目成员失败，失败原因：{response.json().get('message')}")
        except Exception as e:
            st.error(f"无法连接到服务器: {str(e)}")


def project_file_test(headers):
    if st.button("同步项目根路径下的所有文件元数据"):
        try:
            project_id = 'c7ed4e03-208e-451c-ba2d-f3e752ada169'
            data = {
                "file_list": scan_folder_for_file_metadata(folder_path=st.session_state.
                                                           get('selected_project').
                                                           get('path'))
            }
            response = requests.post(
                url=f"{BASE_URL}/projects/{project_id}/files/sync",
                headers=headers,
                data=json.dumps(data)
            )
            if response.status_code == 201:
                st.success(response.json().get("message"))
            else:
                st.error(f"同步项目根路径下的所有文件元数据失败，失败原因：{response.json().get('message')}")
        except Exception as e:
            st.error(f"无法连接到服务器: {str(e)}")
    if st.button("获取项目文件列表"):
        try:
            project_id = 'c7ed4e03-208e-451c-ba2d-f3e752ada169'
            response = requests.get(
                url=f"{BASE_URL}/projects/{project_id}/files",
                headers=headers
            )
            if response.status_code == 200:
                st.success(response.json().get("message"))
                for file in response.json().get("data"):
                    for k, v in file.items():
                        st.write(f"{k}: {v}")
            else:
                st.error(f"获取项目文件列表失败，失败原因：{response.json().get('message')}")
        except Exception as e:
            st.error(f"无法连接到服务器: {str(e)}")
    if st.button("基于当前项目文件内容，创建一个版本快照"):
        try:
            project_id = 'c7ed4e03-208e-451c-ba2d-f3e752ada169'
            data = {
                "name": "这是一个测试版本快照名称",
                "description": "这是一个测试版本快照描述"
            }
            response = requests.post(
                url=f"{BASE_URL}/projects/{project_id}/versions",
                headers=headers,
                data=json.dumps(data)
            )
            if response.status_code == 201:
                st.success(response.json().get("message"))
                snapshot_id = response.json().get("data").get("snapshot_id")
                created_at = response.json().get("data").get("created_at")

                def upload_single_file(file_path, project_root_path):
                    try:
                        # 流式读取，不全部载入内存（单requests仍会暂存body）
                        with open(file_path, "rb") as f:
                            content = f.read().decode("utf-8", "ignore")
                        import os
                        # 需要将文件的绝对路径转换成项目中的相对路径
                        file_abs = Path(file_path).resolve()
                        relative_path = file_abs.relative_to(
                            Path(project_root_path).resolve()
                        )
                        resp = requests.post(
                            url=f"{BASE_URL}/projects/{project_id}/versions/upload-chunk",
                            headers=headers,
                            data=json.dumps({
                                "snapshot_id": snapshot_id,
                                "file_path": str(relative_path),
                                "content": content,
                                "created_at": created_at
                            })
                        )
                        # 模拟耗时，便于调试观察异步是否生效
                        time.sleep(2)
                        return resp.status_code == 201, "上传成功"
                    except Exception as e:
                        return False, "失败原因是：" + str(e)

                # 启动子线程异步上传文件
                all_files = [str(p) for p in Path(st.session_state.get('selected_project').get('path')).rglob("*")
                             if p.is_file()]
                success_sync_file_count = 0
                total_file_count = len(all_files)
                progress_bar = st.progress(0, text="开始上传")
                status_container = st.container()
                # 最多并发同时上传5个文件内容，防止OOM
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = {
                        executor.submit(
                            upload_single_file,
                            file_path,
                            st.session_state.get('selected_project').get('path')
                        ): file_path
                        for file_path in all_files
                    }
                    for future in as_completed(futures):
                        success, message = future.result()
                        with status_container:
                            if success:
                                success_sync_file_count += 1
                        # 更新进度条
                        progress_percent = success_sync_file_count / total_file_count
                        progress_bar.progress(
                            progress_percent,
                            text=f"上传进度: {success_sync_file_count}/{total_file_count} ({int(progress_percent * 100)}%)"
                        )
                progress_bar.progress(1.0, text=f"上传完成！成功：{success_sync_file_count}/{total_file_count}")
                # streamlit是单线程，这里不增加子线程轮询任务状态了，有点复杂，在界面上显示上传进度即可

            else:
                st.error(f"基于当前项目文件内容，创建一个版本快照失败，失败原因：{response.json().get('message')}")
        except Exception as e:
            st.error(f"无法连接到服务器: {str(e)}")

    if st.button("删除某个版本快照"):
        try:
            project_id = 'c7ed4e03-208e-451c-ba2d-f3e752ada169'
            snapshot_id = '8a2d1c4b-adcf-4ddc-a9c5-68285ce97ae4'
            response = requests.delete(
                url=f"{BASE_URL}/projects/{project_id}/versions",
                headers=headers,
                data=json.dumps({
                    "snapshot_id": snapshot_id
                })
            )
            if response.status_code == 200:
                st.success(response.json().get("message"))
            else:
                st.error(f"删除某个版本快照失败，失败原因：{response.json().get('message')}")
        except Exception as e:
            st.error(f"无法连接到服务器: {str(e)}")

    if st.button("获取项目的所有版本快照列表"):
        try:
            project_id = 'c7ed4e03-208e-451c-ba2d-f3e752ada169'
            response = requests.get(
                url=f"{BASE_URL}/projects/{project_id}/versions",
                headers=headers
            )
            if response.status_code == 200:
                st.success(response.json().get("message"))
                for snapshot in response.json().get("data"):
                    for k, v in snapshot.items():
                        st.write(f"{k}: {v}")
            else:
                st.error(f"获取项目的所有版本快照列表失败，失败原因：{response.json().get('message')}")
        except Exception as e:
            st.error(f"无法连接到服务器: {str(e)}")

    if st.button("获取某个版本快照详情信息"):
        try:
            project_id = 'c7ed4e03-208e-451c-ba2d-f3e752ada169'
            snapshot_id = '25eff133-bf54-4356-8da9-093e30bb7df7'
            response = requests.get(
                url=f"{BASE_URL}/projects/{project_id}/versions/{snapshot_id}",
                headers=headers
            )
            if response.status_code == 200:
                st.success(response.json().get("message"))
                for k, v in response.json().get("data").items():
                    st.write(f"{k}: {v}")
                code_file_info_list = response.json().get("data").get("file_list_info")
                version_ids = []
                code_file_paths = []
                code_file_sizes = []
                for code_file_info in code_file_info_list:
                    code_file_sizes.append(code_file_info.get("file_size"))
                    code_file_paths.append(code_file_info.get("file_path"))
                    version_ids.append(code_file_info.get("code_file_version_id"))
                    file_id = code_file_info.get("code_file_id")
                st.write("以下是此版本快照的随机某个文件版本详情")
                try:
                    from random import randint
                    random_index = randint(0, len(version_ids) - 1)
                    version_id = version_ids[random_index]
                    response = requests.get(
                        url=f"{BASE_URL}/projects/{project_id}/files/{version_id}",
                        headers=headers
                    )
                    if response.status_code == 200:
                        st.success(response.json().get("message"))
                        st.write(f"文件路径：{code_file_paths[random_index]}")
                        st.write(f"文件大小：{code_file_sizes[random_index]}")
                        for k, v in response.json().get("data").items():
                            if k == "content":
                                st.write(f"文件内容：")
                                st.code(v)
                            else:
                                st.write(f"{k}: {v}")
                    else:
                        st.error(f"获取某个版本快照的某个文件内容失败，失败原因：{response.json().get('message')}")
                except Exception as e:
                    st.error(f"无法连接到服务器: {str(e)}")

            else:
                st.error(f"获取某个版本快照详情信息失败，失败原因：{response.json().get('message')}")
        except Exception as e:
            st.error(f"无法连接到服务器: {str(e)}")

    if st.button("删除某个被快照引用的文件："):
        try:
            project_id = 'c7ed4e03-208e-451c-ba2d-f3e752ada169'
            file_id = 'ada4ecac-4ee7-4ad5-8e7d-fb8f896a2ca2'
            response = requests.delete(
                url=f"{BASE_URL}/projects/{project_id}/files/{file_id}",
                headers=headers
            )
            if response.status_code == 200:
                st.success(response.json().get("message"))
            else:
                st.error(f"删除某个被快照引用的文件失败，失败原因：{response.json().get('message')}")
        except Exception as e:
            st.error(f"无法连接到服务器: {str(e)}")

    if st.button("删除某个单独的文件"):
        try:
            project_id = 'c7ed4e03-208e-451c-ba2d-f3e752ada169'
            file_id = 'a3abce13-f0a6-423f-84d5-8401c9b33341'    # 需要修改成数据库中孤立的文件id
            response = requests.delete(
                url=f"{BASE_URL}/projects/{project_id}/files/{file_id}",
                headers=headers
            )
            if response.status_code == 200:
                st.success(response.json().get("message"))
        except Exception as e:
            st.error(f"无法连接到服务器: {str(e)}")


def project_review_task_manage_test(headers):
    if st.button("创建项目代码审核任务"):
        try:
            project_id = 'c7ed4e03-208e-451c-ba2d-f3e752ada169'
            response = requests.post(
                url=f"{BASE_URL}/projects/{project_id}/tasks",
                headers=headers,
                data=json.dumps({
                    "task_type": "code_review",
                    "task_name": "项目代码审核任务",
                    "task_status": "pending",
                    "task_description": "项目代码审核任务",
                    "task_priority": "normal"
                })
            )
            if response.status_code == 200:
                st.success(response.json().get("message"))
                st.write(f"任务ID：{response.json().get('data').get('task_id')}")
            else:
                st.error(f"创建项目代码审核任务失败，失败原因：{response.json().get('message')}")
        except Exception as e:
            st.error(f"无法连接到服务器: {str(e)}")
    pass
