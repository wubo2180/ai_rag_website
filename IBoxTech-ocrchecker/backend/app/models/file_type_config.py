"""
文件类型配置模型（优化版）
支持多种文件类型的动态配置
- OCR模型关联 model_configs 表
- 存储表配置支持多表 JSON 数组
- 适配器配置支持动态加载
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from . import db


class FileTypeConfig(db.Model):
    """文件类型配置表（优化版）"""
    __tablename__ = 'file_type_configs'
    
    id = Column(Integer, primary_key=True, comment='主键ID')
    
    # ==================== 基本信息 ====================
    type_code = Column(String(50), unique=True, nullable=False, comment='类型代码，如：commission、paper')
    type_name = Column(String(100), nullable=False, comment='类型名称，如：委托单、论文')
    type_description = Column(Text, comment='类型描述')
    
    # ==================== OCR模型配置 ====================
    # 外键关联到 model_configs 表
    model_config_id = Column(
        Integer, 
        ForeignKey('model_configs.id', ondelete='SET NULL', onupdate='CASCADE'),
        comment='OCR模型配置ID（关联model_configs表）'
    )
    
    # OCR特定配置（可选，覆盖model的默认配置）
    ocr_config = Column(
        JSON, 
        comment='OCR特定配置参数（可选），用于覆盖model_configs中的默认配置'
    )
    
    # ==================== 数据存储配置 ====================
    # JSON数组，存储关联的数据表名列表
    # 格式: ["commission_basic", "test_items", "special_tests"]
    storage_tables = Column(
        JSON, 
        nullable=False,
        comment='数据存储表配置（JSON数组），格式：["table1", "table2", ...]'
    )
    
    # ==================== 适配器配置 ====================
    adapter_class = Column(
        String(100), 
        nullable=False,
        comment='适配器类名，如：CommissionAdapter, PaperAdapter'
    )
    
    adapter_module = Column(
        String(200), 
        default='adapters',
        comment='适配器模块路径，默认：adapters'
    )
    
    # ==================== 表单配置 ====================
    form_config = Column(
        JSON, 
        comment='表单配置（JSON格式），定义表单字段和布局'
    )
    
    form_component = Column(
        String(200), 
        comment='前端表单组件路径，如：CommissionForm'
    )
    
    # ==================== 验证规则 ====================
    validation_rules = Column(
        JSON, 
        comment='数据验证规则（JSON格式）'
    )
    
    # ==================== 状态字段 ====================
    is_active = Column(
        Boolean, 
        default=True, 
        nullable=False, 
        comment='是否启用'
    )
    
    sort_order = Column(
        Integer, 
        default=0, 
        comment='排序序号'
    )
    
    # ==================== 系统字段 ====================
    created_at = Column(
        DateTime, 
        nullable=False, 
        default=datetime.utcnow, 
        comment='创建时间'
    )
    
    updated_at = Column(
        DateTime, 
        nullable=False, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        comment='更新时间'
    )
    
    # ==================== 关系 ====================
    # 关联到 model_configs 表
    model_config = relationship(
        'ModelConfig',
        foreign_keys=[model_config_id],
        backref='file_types'
    )
    
    def __repr__(self):
        return f'<FileTypeConfig {self.type_code}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'type_code': self.type_code,
            'type_name': self.type_name,
            'type_description': self.type_description,
            
            # OCR配置
            'model_config_id': self.model_config_id,
            'model_config': self.model_config.to_dict() if self.model_config else None,
            'ocr_config': self.ocr_config,
            
            # 存储配置
            'storage_tables': self.storage_tables,
            
            # 适配器配置
            'adapter_class': self.adapter_class,
            'adapter_module': self.adapter_module,
            
            # 表单配置
            'form_config': self.form_config,
            'form_component': self.form_component,
            
            # 验证规则
            'validation_rules': self.validation_rules,
            
            # 状态
            'is_active': self.is_active,
            'sort_order': self.sort_order,
            
            # 系统字段
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    # ==================== 便捷方法 ====================
    
    def get_storage_table_by_role(self, role: str) -> str:
        """
        根据角色获取存储表名（已废弃，保留用于向后兼容）
        
        Args:
            role: 表的角色，如：basic, items, details, ocr_results
            
        Returns:
            表名，如果找不到返回 None
        """
        # 新格式：storage_tables 是字符串数组
        if not self.storage_tables:
            return None
        
        # 兼容旧格式（对象数组）
        if isinstance(self.storage_tables, list) and len(self.storage_tables) > 0:
            if isinstance(self.storage_tables[0], dict):
                # 旧格式：[{"role":"basic","table":"..."}]
                for table_config in self.storage_tables:
                    if table_config.get('role') == role:
                        return table_config.get('table')
            elif isinstance(self.storage_tables[0], str):
                # 新格式：["table1", "table2"]
                # 按索引映射角色
                role_index_map = {
                    'basic': 0,
                    'items': 1,
                    'details': 2,
                    'ocr_results': 3
                }
                index = role_index_map.get(role)
                if index is not None and index < len(self.storage_tables):
                    return self.storage_tables[index]
        
        return None
    
    def get_all_storage_tables(self) -> list:
        """
        获取所有存储表名列表
        
        Returns:
            表名列表
        """
        if not self.storage_tables:
            return []
        
        # 新格式：直接返回字符串数组
        if isinstance(self.storage_tables[0], str):
            return self.storage_tables
        
        # 兼容旧格式：从对象数组中提取表名
        return [table_config.get('table') for table_config in self.storage_tables if table_config.get('table')]
    
    def get_adapter_instance(self):
        """
        动态创建并返回适配器实例
        
        Returns:
            适配器实例
            
        Raises:
            ImportError: 无法加载适配器
        """
        try:
            import importlib
            
            # 导入适配器模块
            module = importlib.import_module(f'app.{self.adapter_module}.{self._get_adapter_module_name()}')
            
            # 获取适配器类
            adapter_class = getattr(module, self.adapter_class)
            
            # 创建实例
            return adapter_class()
        
        except Exception as e:
            raise ImportError(f"无法加载适配器 {self.adapter_class}: {str(e)}")
    
    def _get_adapter_module_name(self) -> str:
        """
        从适配器类名推断模块名
        如：CommissionAdapter -> commission_adapter
        """
        import re
        # 将驼峰命名转换为下划线命名
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', self.adapter_class)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
    
    def merge_ocr_config(self) -> dict:
        """
        合并模型配置和特定OCR配置
        
        Returns:
            合并后的完整OCR配置
        """
        merged_config = {}
        
        # 先加载模型的默认配置
        if self.model_config and self.model_config.config_params:
            merged_config.update(self.model_config.config_params)
        
        # 再覆盖特定配置
        if self.ocr_config:
            merged_config.update(self.ocr_config)
        
        return merged_config
    
    # ==================== 兼容性方法（保留旧代码兼容） ====================
    
    @property
    def ocr_model_api(self):
        """兼容性属性：从关联的model_config获取API地址"""
        if self.model_config:
            return self.model_config.api_url
        return None
    
    @property
    def storage_table_basic(self):
        """兼容性属性：获取basic表名"""
        return self.get_storage_table_by_role('basic')
    
    @property
    def storage_table_items(self):
        """兼容性属性：获取items表名"""
        return self.get_storage_table_by_role('items')
    
    @property
    def storage_table_details(self):
        """兼容性属性：获取details表名"""
        return self.get_storage_table_by_role('details')


