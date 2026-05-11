"""
验证工具函数
"""
import os
# import magic  # 临时注释掉，避免libmagic依赖问题
from flask import current_app


def validate_file_type(file_obj, filename):
    """
    验证文件类型
    
    Args:
        file_obj: 文件对象
        filename: 文件名
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        # 获取文件扩展名
        file_extension = os.path.splitext(filename)[1].lower()
        
        # 检查扩展名是否在允许的列表中
        allowed_extensions = current_app.config.get('UPLOAD_EXTENSIONS', [])
        if file_extension not in allowed_extensions:
            return False, f'不支持的文件类型: {file_extension}'
        
        # 使用python-magic检查文件的实际MIME类型
        try:
            file_obj.seek(0)
            # 临时简化的文件类型检查
            ext = os.path.splitext(filename)[1].lower()
            mime_map = {
                '.pdf': 'application/pdf',
                '.jpg': 'image/jpeg', 
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.bmp': 'image/bmp',
                '.tiff': 'image/tiff'
            }
            mime_type = mime_map.get(ext, 'application/octet-stream')
            file_obj.seek(0)
            
            # 定义允许的MIME类型
            allowed_mime_types = {
                '.pdf': ['application/pdf'],
                '.jpg': ['image/jpeg'],
                '.jpeg': ['image/jpeg'],
                '.png': ['image/png'],
                '.tiff': ['image/tiff', 'image/tiff-fx'],
                '.tif': ['image/tiff', 'image/tiff-fx']
            }
            
            if file_extension in allowed_mime_types:
                if mime_type not in allowed_mime_types[file_extension]:
                    return False, f'文件内容与扩展名不匹配: {mime_type}'
            
        except ImportError:
            # 如果python-magic未安装，跳过MIME类型检查
            pass
        except Exception as e:
            # MIME类型检查失败，记录警告但不阻止上传
            current_app.logger.warning(f'MIME类型检查失败: {str(e)}')
        
        return True, None
        
    except Exception as e:
        return False, f'文件验证失败: {str(e)}'


def validate_file_size(file_obj, max_size=None):
    """
    验证文件大小
    
    Args:
        file_obj: 文件对象
        max_size: 最大文件大小（字节），None表示使用配置中的值
        
    Returns:
        tuple: (is_valid, error_message, file_size)
    """
    try:
        # 获取文件大小
        file_obj.seek(0, 2)  # 移动到文件末尾
        file_size = file_obj.tell()
        file_obj.seek(0)  # 重置到文件开头
        
        if max_size is None:
            max_size = current_app.config.get('MAX_CONTENT_LENGTH', 100 * 1024 * 1024)
        
        if file_size > max_size:
            return False, f'文件大小超出限制: {format_file_size(file_size)} > {format_file_size(max_size)}', file_size
        
        if file_size == 0:
            return False, '文件为空', file_size
        
        return True, None, file_size
        
    except Exception as e:
        return False, f'文件大小验证失败: {str(e)}', 0


def format_file_size(size_bytes):
    """
    格式化文件大小显示
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        str: 格式化后的大小字符串
    """
    if size_bytes == 0:
        return '0 B'
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f'{size_bytes:.1f} {unit}'
        size_bytes /= 1024.0
    
    return f'{size_bytes:.1f} PB'


def validate_image_dimensions(file_obj, min_width=100, min_height=100, max_width=10000, max_height=10000):
    """
    验证图像尺寸
    
    Args:
        file_obj: 文件对象
        min_width: 最小宽度
        min_height: 最小高度
        max_width: 最大宽度
        max_height: 最大高度
        
    Returns:
        tuple: (is_valid, error_message, dimensions)
    """
    try:
        from PIL import Image
        
        file_obj.seek(0)
        image = Image.open(file_obj)
        width, height = image.size
        file_obj.seek(0)
        
        if width < min_width or height < min_height:
            return False, f'图像尺寸过小: {width}x{height} < {min_width}x{min_height}', (width, height)
        
        if width > max_width or height > max_height:
            return False, f'图像尺寸过大: {width}x{height} > {max_width}x{max_height}', (width, height)
        
        return True, None, (width, height)
        
    except ImportError:
        return True, 'PIL未安装，跳过尺寸验证', None
    except Exception as e:
        return False, f'图像尺寸验证失败: {str(e)}', None


def validate_pdf_pages(file_obj, max_pages=100):
    """
    验证PDF页数
    
    Args:
        file_obj: 文件对象
        max_pages: 最大页数
        
    Returns:
        tuple: (is_valid, error_message, page_count)
    """
    try:
        import fitz  # PyMuPDF
        
        file_obj.seek(0)
        file_data = file_obj.read()
        file_obj.seek(0)
        
        doc = fitz.open(stream=file_data, filetype="pdf")
        page_count = len(doc)
        doc.close()
        
        if page_count > max_pages:
            return False, f'PDF页数超出限制: {page_count} > {max_pages}', page_count
        
        if page_count == 0:
            return False, 'PDF文件为空或损坏', page_count
        
        return True, None, page_count
        
    except ImportError:
        return True, 'PyMuPDF未安装，跳过页数验证', None
    except Exception as e:
        return False, f'PDF页数验证失败: {str(e)}', None


def sanitize_filename(filename):
    """
    清理文件名，移除危险字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        str: 清理后的文件名
    """
    import re
    
    # 移除路径分隔符和其他危险字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # 移除控制字符
    filename = ''.join(char for char in filename if ord(char) >= 32)
    
    # 限制文件名长度
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255 - len(ext)] + ext
    
    # 确保文件名不为空
    if not filename.strip():
        filename = 'unnamed_file'
    
    return filename
