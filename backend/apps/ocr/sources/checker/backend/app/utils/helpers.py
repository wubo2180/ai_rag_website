"""
辅助工具函数
"""
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


def generate_batch_id():
    """
    生成批次ID
    
    Returns:
        str: UUID格式的批次ID
    """
    return str(uuid.uuid4())


def generate_uuid():
    """
    生成UUID
    
    Returns:
        str: UUID字符串
    """
    return str(uuid.uuid4())


def generate_random_string(length=32):
    """
    生成随机字符串
    
    Args:
        length: 字符串长度
        
    Returns:
        str: 随机字符串
    """
    return secrets.token_urlsafe(length)


def get_file_extension(filename):
    """
    获取文件扩展名
    
    Args:
        filename: 文件名
        
    Returns:
        str: 文件扩展名（小写，包含点号）
    """
    return filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''


def calculate_file_hash(file_obj, algorithm='md5'):
    """
    计算文件哈希值
    
    Args:
        file_obj: 文件对象
        algorithm: 哈希算法（md5, sha1, sha256）
        
    Returns:
        str: 文件哈希值
    """
    if algorithm == 'md5':
        hash_obj = hashlib.md5()
    elif algorithm == 'sha1':
        hash_obj = hashlib.sha1()
    elif algorithm == 'sha256':
        hash_obj = hashlib.sha256()
    else:
        raise ValueError(f'不支持的哈希算法: {algorithm}')
    
    # 读取文件内容并计算哈希
    file_obj.seek(0)
    for chunk in iter(lambda: file_obj.read(4096), b""):
        hash_obj.update(chunk)
    file_obj.seek(0)
    
    return hash_obj.hexdigest()


def format_datetime(dt, format_string='%Y-%m-%d %H:%M:%S'):
    """
    格式化日期时间
    
    Args:
        dt: datetime对象
        format_string: 格式字符串
        
    Returns:
        str: 格式化后的日期时间字符串
    """
    if dt is None:
        return None
    
    if isinstance(dt, str):
        return dt
    
    return dt.strftime(format_string)


def parse_datetime(date_string, format_string='%Y-%m-%d %H:%M:%S'):
    """
    解析日期时间字符串
    
    Args:
        date_string: 日期时间字符串
        format_string: 格式字符串
        
    Returns:
        datetime: datetime对象
    """
    if date_string is None:
        return None
    
    if isinstance(date_string, datetime):
        return date_string
    
    return datetime.strptime(date_string, format_string)


def calculate_time_ago(dt):
    """
    计算时间差的人性化表示
    
    Args:
        dt: datetime对象
        
    Returns:
        str: 人性化的时间差表示
    """
    if dt is None:
        return '未知'
    
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 365:
        return f'{diff.days // 365}年前'
    elif diff.days > 30:
        return f'{diff.days // 30}个月前'
    elif diff.days > 0:
        return f'{diff.days}天前'
    elif diff.seconds > 3600:
        return f'{diff.seconds // 3600}小时前'
    elif diff.seconds > 60:
        return f'{diff.seconds // 60}分钟前'
    else:
        return '刚刚'


def chunk_list(lst, chunk_size):
    """
    将列表分割为指定大小的块
    
    Args:
        lst: 要分割的列表
        chunk_size: 每块的大小
        
    Yields:
        list: 列表块
    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def safe_json_loads(json_string, default=None):
    """
    安全地解析JSON字符串
    
    Args:
        json_string: JSON字符串
        default: 解析失败时的默认值
        
    Returns:
        解析后的对象或默认值
    """
    try:
        import json
        return json.loads(json_string)
    except (ValueError, TypeError, json.JSONDecodeError):
        return default


def safe_json_dumps(obj, default=None):
    """
    安全地序列化为JSON字符串
    
    Args:
        obj: 要序列化的对象
        default: 序列化失败时的默认值
        
    Returns:
        str: JSON字符串或默认值
    """
    try:
        import json
        return json.dumps(obj, ensure_ascii=False)
    except (ValueError, TypeError):
        return default


def merge_dicts(*dicts):
    """
    合并多个字典
    
    Args:
        *dicts: 要合并的字典
        
    Returns:
        dict: 合并后的字典
    """
    result = {}
    for d in dicts:
        if d:
            result.update(d)
    return result


def get_nested_value(data, key_path, default=None):
    """
    从嵌套字典中获取值
    
    Args:
        data: 数据字典
        key_path: 键路径，如 'user.profile.name'
        default: 默认值
        
    Returns:
        获取到的值或默认值
    """
    try:
        keys = key_path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    except (AttributeError, KeyError, TypeError):
        return default


def set_nested_value(data, key_path, value):
    """
    在嵌套字典中设置值
    
    Args:
        data: 数据字典
        key_path: 键路径，如 'user.profile.name'
        value: 要设置的值
        
    Returns:
        bool: 是否设置成功
    """
    try:
        keys = key_path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
        return True
    except (AttributeError, KeyError, TypeError):
        return False


def validate_email(email):
    """
    验证邮箱地址格式
    
    Args:
        email: 邮箱地址
        
    Returns:
        bool: 是否为有效邮箱
    """
    import re
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def truncate_string(text, max_length, suffix='...'):
    """
    截断字符串
    
    Args:
        text: 原始字符串
        max_length: 最大长度
        suffix: 截断后缀
        
    Returns:
        str: 截断后的字符串
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def create_response(success=True, message='', data=None, code=200):
    """
    创建标准化的API响应
    
    Args:
        success: 是否成功
        message: 响应消息
        data: 响应数据
        code: HTTP状态码
        
    Returns:
        tuple: (response_dict, status_code)
    """
    response = {
        'success': success,
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response['data'] = data
    
    return response, code
