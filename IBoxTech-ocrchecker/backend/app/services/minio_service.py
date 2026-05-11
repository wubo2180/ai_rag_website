"""
MinIO对象存储服务
"""
import io
import uuid
import hashlib
from minio import Minio
from minio.error import S3Error
from flask import current_app
import mimetypes
import os
from urllib.parse import urljoin


class MinioService:
    """MinIO服务类"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化MinIO客户端"""
        try:
            self.client = Minio(
                current_app.config['MINIO_ENDPOINT'],
                access_key=current_app.config['MINIO_ACCESS_KEY'],
                secret_key=current_app.config['MINIO_SECRET_KEY'],
                secure=current_app.config['MINIO_SECURE']
            )
            
            # 检查并创建存储桶
            bucket_name = current_app.config['MINIO_BUCKET_NAME']
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                current_app.logger.info(f'创建存储桶: {bucket_name}')
                
        except Exception as e:
            current_app.logger.error(f'MinIO初始化失败: {str(e)}')
            raise e
    
    def upload_file(self, file_obj, filename, content_type=None, folder='files'):
        """
        上传文件到MinIO
        
        Args:
            file_obj: 文件对象
            filename: 原始文件名
            content_type: 文件MIME类型
            folder: 存储文件夹
            
        Returns:
            dict: 上传结果信息
        """
        try:
            # 生成唯一的存储文件名
            file_extension = os.path.splitext(filename)[1]
            stored_filename = f"{uuid.uuid4().hex}{file_extension}"
            object_name = f"{folder}/{stored_filename}"
            
            # 读取文件内容并计算MD5
            file_content = file_obj.read()
            file_obj.seek(0)  # 重置文件指针
            
            md5_hash = hashlib.md5(file_content).hexdigest()
            file_size = len(file_content)
            
            # 自动检测MIME类型
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    content_type = 'application/octet-stream'
            
            # 上传文件
            result = self.client.put_object(
                bucket_name=current_app.config['MINIO_BUCKET_NAME'],
                object_name=object_name,
                data=io.BytesIO(file_content),
                length=file_size,
                content_type=content_type
            )
            
            current_app.logger.info(f'文件上传成功: {object_name}')
            
            return {
                'success': True,
                'stored_filename': stored_filename,
                'object_name': object_name,
                'file_size': file_size,
                'md5_hash': md5_hash,
                'content_type': content_type,
                'etag': result.etag
            }
            
        except S3Error as e:
            current_app.logger.error(f'MinIO上传失败: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            current_app.logger.error(f'文件上传异常: {str(e)}')
            return {
                'success': False,
                'error': str(e)
            }
    
    def download_file(self, object_name):
        """
        从MinIO下载文件
        
        Args:
            object_name: 对象名称
            
        Returns:
            file_data: 文件数据流
        """
        try:
            response = self.client.get_object(
                bucket_name=current_app.config['MINIO_BUCKET_NAME'],
                object_name=object_name
            )
            
            return response.data
            
        except S3Error as e:
            current_app.logger.error(f'MinIO下载失败: {str(e)}')
            return None
        except Exception as e:
            current_app.logger.error(f'文件下载异常: {str(e)}')
            return None
    
    def delete_file(self, object_name):
        """
        从MinIO删除文件
        
        Args:
            object_name: 对象名称
            
        Returns:
            bool: 删除结果
        """
        try:
            self.client.remove_object(
                bucket_name=current_app.config['MINIO_BUCKET_NAME'],
                object_name=object_name
            )
            
            current_app.logger.info(f'文件删除成功: {object_name}')
            return True
            
        except S3Error as e:
            current_app.logger.error(f'MinIO删除失败: {str(e)}')
            return False
        except Exception as e:
            current_app.logger.error(f'文件删除异常: {str(e)}')
            return False
    
    def get_file_url(self, object_name, expires=3600):
        """
        获取文件的预签名URL
        
        Args:
            object_name: 对象名称
            expires: 过期时间（秒）
            
        Returns:
            str: 预签名URL
        """
        try:
            current_app.logger.info(f'正在生成预签名URL: {object_name}, expires: {expires}秒')
            
            url = self.client.presigned_get_object(
                bucket_name=current_app.config['MINIO_BUCKET_NAME'],
                object_name=object_name,
                expires=expires
            )
            
            current_app.logger.info(f'预签名URL生成成功: {url[:100]}...')
            return url
            
        except S3Error as e:
            current_app.logger.error(f'获取预签名URL失败: {str(e)}')
            current_app.logger.error(f'MinIO配置: endpoint={current_app.config.get("MINIO_ENDPOINT")}, bucket={current_app.config.get("MINIO_BUCKET_NAME")}')
            return None
        except Exception as e:
            current_app.logger.error(f'获取预签名URL异常: {str(e)}')
            current_app.logger.error(f'对象名称: {object_name}')
            return None
    
    def file_exists(self, object_name):
        """
        检查文件是否存在
        
        Args:
            object_name: 对象名称
            
        Returns:
            bool: 文件是否存在
        """
        try:
            self.client.stat_object(
                bucket_name=current_app.config['MINIO_BUCKET_NAME'],
                object_name=object_name
            )
            return True
            
        except S3Error:
            return False
        except Exception as e:
            current_app.logger.error(f'检查文件存在异常: {str(e)}')
            return False
    
    def get_file_info(self, object_name):
        """
        获取文件信息
        
        Args:
            object_name: 对象名称
            
        Returns:
            dict: 文件信息
        """
        try:
            stat = self.client.stat_object(
                bucket_name=current_app.config['MINIO_BUCKET_NAME'],
                object_name=object_name
            )
            
            return {
                'object_name': object_name,
                'size': stat.size,
                'etag': stat.etag,
                'content_type': stat.content_type,
                'last_modified': stat.last_modified,
                'metadata': stat.metadata
            }
            
        except S3Error as e:
            current_app.logger.error(f'获取文件信息失败: {str(e)}')
            return None
        except Exception as e:
            current_app.logger.error(f'获取文件信息异常: {str(e)}')
            return None
    
    def list_files(self, prefix='', max_keys=1000):
        """
        列出文件
        
        Args:
            prefix: 文件名前缀
            max_keys: 最大返回数量
            
        Returns:
            list: 文件列表
        """
        try:
            objects = self.client.list_objects(
                bucket_name=current_app.config['MINIO_BUCKET_NAME'],
                prefix=prefix,
                max_keys=max_keys
            )
            
            files = []
            for obj in objects:
                files.append({
                    'object_name': obj.object_name,
                    'size': obj.size,
                    'etag': obj.etag,
                    'last_modified': obj.last_modified
                })
            
            return files
            
        except S3Error as e:
            current_app.logger.error(f'列出文件失败: {str(e)}')
            return []
        except Exception as e:
            current_app.logger.error(f'列出文件异常: {str(e)}')
            return []
    
    def batch_delete_files(self, object_names):
        """
        批量删除文件
        
        Args:
            object_names: 对象名称列表
            
        Returns:
            dict: 删除结果
        """
        try:
            from minio.deleteobjects import DeleteObject
            
            delete_objects = [DeleteObject(name) for name in object_names]
            errors = self.client.remove_objects(
                bucket_name=current_app.config['MINIO_BUCKET_NAME'],
                delete_object_list=delete_objects
            )
            
            error_list = list(errors)
            success_count = len(object_names) - len(error_list)
            
            return {
                'success_count': success_count,
                'error_count': len(error_list),
                'errors': [str(error) for error in error_list]
            }
            
        except Exception as e:
            current_app.logger.error(f'批量删除文件异常: {str(e)}')
            return {
                'success_count': 0,
                'error_count': len(object_names),
                'errors': [str(e)]
            }
