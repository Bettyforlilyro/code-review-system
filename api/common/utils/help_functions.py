import hashlib
from typing import Union


def deterministic_hash(
    data: Union[str, bytes],
    algorithm: str = "sha256",
    encoding: str = "utf-8"
) -> str:
    """
    对字符串或字节计算确定性哈希值（相同内容始终返回相同 hash）。

    参数:
        data (str | bytes): 要哈希的数据。
        algorithm (str): 哈希算法，如 'sha256', 'md5', 'sha1' 等（推荐 'sha256'）。
        encoding (str): 字符串编码方式（仅当 data 是 str 时使用）。

    返回:
        str: 十六进制字符串形式的哈希值（小写）。

    """
    if isinstance(data, str):
        data = data.encode(encoding)
    elif not isinstance(data, bytes):
        raise TypeError("data must be str or bytes")

    try:
        hasher = hashlib.new(algorithm)
    except ValueError as e:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}") from e

    hasher.update(data)
    return hasher.hexdigest()


def format_file_size(size_bytes):
    """
    将字节数转换为可读的文件大小。

    参数:
        size_bytes (int): 文件大小（字节）。

    返回:
        str: 文件大小，如 "10B", "2.5KB", "1.23MB" 等。

    """
    if size_bytes == 0:
        return "0B"
    size_units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(size_bytes)
    while size >= 1024 and unit_index < len(size_units) - 1:
        size /= 1024.0
        unit_index += 1
    if size == int(size) or size >= 100:
        return f"{int(size)}{size_units[unit_index]}"
    else:
        return f"{size:.1f}{size_units[unit_index]}"

