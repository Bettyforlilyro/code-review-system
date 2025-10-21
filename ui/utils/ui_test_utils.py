# ui_test_utils.py
import json
import hashlib
import os
from pathlib import Path
from typing import Union


def hash_password(password: str) -> str:
    """密码哈希函数"""
    return hashlib.sha256(password.encode()).hexdigest()


def save_json(data: dict, filepath: Path) -> None:
    """保存JSON数据"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(filepath: Path) -> dict:
    """加载JSON数据"""
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def get_user_file(username: str) -> Path:
    """获取用户数据文件路径"""
    return Path("/home/zhy/workspace/code-review-system/test_projects") / f"{username}.json"


def get_user_projects_dir(username: str) -> Path:
    """获取用户项目目录"""
    user_dir = Path("/home/zhy/workspace/code-review-system/test_projects") / username
    user_dir.mkdir(exist_ok=True)
    return user_dir


def build_directory_tree_recursive(directory: Union[str, Path]) -> dict:
    """递归获取目录树结构"""
    if isinstance(directory, str):
        directory = Path(directory)
    if directory.is_file():
        return {
            "name": directory.name,     # 文件名
            "path": str(directory),     # 包含文件名的路径
            "type": "file",
            "children": [],
            "expanded": False
        }
    else:
        children = []
        for child in sorted(directory.iterdir()):
            if child.name.startswith('.'):
                continue    # 跳过隐藏文件
            children.append(build_directory_tree_recursive(child))
        return {
            "name": directory.name,
            "path": str(directory),
            "type": "directory",
            "children": children,
            "expanded": False       # 默认不展开
        }


def is_text_file(file_path: Union[str, Path]) -> bool:
    """判断文件是否为文本文件"""
    try:
        if isinstance(file_path, str):
            file_path = Path(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)
        return True
    except UnicodeDecodeError:
        return False


def delete_tree_node_with_path(root: dict, specify_path: str):
    """
    从多叉树中删除指定路径的节点及其所有子节点

    Args:
        root: 多叉树的根节点（字典）
        specify_path: 要删除的节点路径

    Returns:
        删除指定节点后的多叉树根节点，如果根节点被删除则返回None
    """
    # 如果根结点就是要删除的结点
    if root.get("path") == specify_path:
        return None

    def dfs_delete_optimized(node):
        """
        深度优先搜索，找到目标后提前终止
        """
        children = node.get("children", [])

        # 首先检查直接子节点中是否有目标
        for i, child in enumerate(children):
            if child.get("path") == specify_path:
                # 找到目标，删除这个子节点
                node["children"] = children[:i] + children[i + 1:]
                return True, node

        # 如果没有直接子节点是目标，递归搜索
        for i, child in enumerate(children):
            found, updated_child = dfs_delete_optimized(child)
            if found:
                # 更新子节点
                children[i] = updated_child
                node["children"] = children
                return True, node

        return False, node

    found, result = dfs_delete_optimized(root)
    return result


def get_project_files(project_directory: Union[str, Path]) -> list:
    """获取项目中的文件列表，project_directory必须是当前文件全路径，str与Path类型均可"""
    if isinstance(project_directory, str):
        project_directory = Path(project_directory)
    if not project_directory.exists():
        return []

    files = []
    for file_path in project_directory.rglob("*"):
        if file_path.is_file():
            files.append({
                "name": file_path.name,
                "path": str(file_path),
                "relative_path": str(file_path.relative_to(project_directory)),
                "size": file_path.stat().st_size
            })
    return files


def _do_update_directory_expansion(node: dict, path: str, expanded: bool):
    if node["type"] == "directory" and node["path"] == path:
        node["expanded"] = expanded
        return
    for child in node["children"]:
        _do_update_directory_expansion(child, path, expanded)


def add_node_to_directory_tree(node: dict, path: str, name: str, is_file: bool):
    """向目录树中添加节点"""
    if node["type"] == "directory" and node["path"] == path:
        node["children"].append({
            "name": name,
            "path": os.path.join(path, name),
            "type": "file" if is_file else "directory",
            "children": [],
            "expanded": False   # 默认不展开
        })
        return
    for child in node["children"]:
        add_node_to_directory_tree(child, path, name, is_file)
