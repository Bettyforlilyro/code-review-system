import os
from datetime import datetime
from pathlib import Path

# 常见文本文件扩展名映射到 language
TEXT_EXTENSIONS = {
    '.txt': 'text',
    '.md': 'markdown',
    '.rst': 'restructuredtext',
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.java': 'java',
    '.c': 'c',
    '.cpp': 'cpp',
    '.h': 'c',
    '.hpp': 'cpp',
    '.cs': 'csharp',
    '.go': 'go',
    '.rs': 'rust',
    '.rb': 'ruby',
    '.php': 'php',
    '.html': 'html',
    '.htm': 'html',
    '.xml': 'xml',
    '.json': 'json',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.toml': 'toml',
    '.ini': 'ini',
    '.sql': 'sql',
    '.sh': 'shell',
    '.bash': 'shell',
    '.zsh': 'shell',
    '.css': 'css',
    '.scss': 'scss',
    '.less': 'less',
    '.swift': 'swift',
    '.kt': 'kotlin',
    '.scala': 'scala',
    '.pl': 'perl',
    '.lua': 'lua',
    '.r': 'r',
    '.m': 'matlab',  # 或 objective-c，根据项目可调整
    '.mm': 'objective-c++',
    '.swift': 'swift',
    # 可继续扩展
}


def is_binary_file(file_detail_path: Path) -> bool:
    """
    判断文件是否为二进制文件。
    方法：尝试读取前1024字节，看是否包含空字节或大量非文本字符。
    """
    try:
        with open(file_detail_path, 'rb') as f:
            chunk = f.read(1024)
            if b'\x00' in chunk:
                return True  # 有空字节，很可能是二进制
            # 尝试解码为 UTF-8（或系统默认编码）
            try:
                chunk.decode('utf-8')
                return False
            except UnicodeDecodeError:
                return True
    except (OSError, IOError):
        # 无法读取的文件（如权限不足）视为二进制或跳过，这里保守视为二进制
        return True


def scan_folder_for_file_metadata(folder_path: str) -> list[dict]:
    """
    递归扫描指定文件夹中的所有文件，返回每个文件的元数据列表。

    Args:
        folder_path (str): 要扫描的文件夹路径。

    Returns:
        list[dict]: 每个元素是一个包含文件元数据的字典。
    """
    result = []
    folder = Path(folder_path)

    if not folder.exists():
        raise FileNotFoundError(f"指定的文件夹不存在: {folder_path}")
    if not folder.is_dir():
        raise NotADirectoryError(f"指定的路径不是文件夹: {folder_path}")

    # 递归遍历所有文件
    for file_path in folder.rglob('*'):
        if file_path.is_file():
            try:
                stat = file_path.stat()
                size = stat.st_size
                mtime = datetime.fromtimestamp(stat.st_mtime).isoformat()
                # 判断是否二进制
                binary = is_binary_file(file_path)
                # 推断 language
                language = 'unknown'
                if not binary:
                    ext = file_path.suffix.lower()
                    language = TEXT_EXTENSIONS.get(ext, 'text')  # 默认为 text
                # 构造相对路径（相对于输入的 folder_path）
                # 如果你希望是绝对路径，可改为 str(file_path.resolve())
                relative_path = file_path.relative_to(folder)
                file_path_str = str(relative_path).replace(os.sep, '/')  # 统一用 / 分隔
                result.append({
                    "file_path": file_path_str,
                    "file_size": size,
                    "last_modified": mtime,
                    "is_binary": binary,
                    "language": language
                })
            except (OSError, IOError) as e:
                # 跳过无法访问的文件（如权限问题）
                print(f"警告: 无法读取文件 {file_path}: {e}")
                continue

    return result


def scan_folder_for_file_content(folder_path: str) -> list[dict]:
    result = []
    folder = Path(folder_path)

    if not folder.exists():
        raise FileNotFoundError(f"指定的文件夹不存在: {folder_path}")
    if not folder.is_dir():
        raise NotADirectoryError(f"指定的路径不是文件夹: {folder_path}")

    return result
