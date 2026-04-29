"""
数据模型模块
"""
from flask_sqlalchemy import SQLAlchemy

# 创建统一的数据库实例
db = SQLAlchemy()

# 延迟导入模型以避免循环引用
def get_models():
    """获取所有模型类"""
    from .user import User
    from .file import File
    from .ocr_result import OCRResult
    from .review_record import ReviewRecord  
    from .file_assignment import FileAssignment
    from .commission import CommissionBasic, TestItem, SpecialTest, CommissionOcrResult
    from .model_config import ModelConfig
    from .ocr_task import OcrTask
    
    # 尝试导入新的文档导入模型（如果存在）
    try:
        from .commission_document import CommissionDocument, CommissionExtractedField, CommissionStatistics
        has_document_models = True
    except ImportError:
        CommissionDocument = None
        CommissionExtractedField = None
        CommissionStatistics = None
        has_document_models = False
    
    # 尝试导入文件类型配置模型（新增）
    try:
        from .file_type_config import FileTypeConfig
        has_file_type_config = True
    except ImportError:
        FileTypeConfig = None
        has_file_type_config = False
    
    # 尝试导入论文数据模型（新增）
    try:
        from .paper_article import PaperArticle
        from .paper_material_intermediate import PaperMaterialIntermediate
        from .paper_property import PaperProperty
        has_paper_models = True
    except ImportError:
        PaperArticle = None
        PaperMaterialIntermediate = None
        PaperProperty = None
        has_paper_models = False
    
    models = {
        'User': User,
        'File': File,
        'OCRResult': OCRResult, 
        'ReviewRecord': ReviewRecord,
        'FileAssignment': FileAssignment,
        'CommissionBasic': CommissionBasic,
        'TestItem': TestItem,
        'SpecialTest': SpecialTest,
        'CommissionOcrResult': CommissionOcrResult,
        'ModelConfig': ModelConfig,
        'OcrTask': OcrTask
    }
    
    # 添加文档导入模型（如果存在）
    if has_document_models:
        models['CommissionDocument'] = CommissionDocument
        models['CommissionExtractedField'] = CommissionExtractedField
        models['CommissionStatistics'] = CommissionStatistics
    
    # 添加文件类型配置模型（如果存在）
    if has_file_type_config:
        models['FileTypeConfig'] = FileTypeConfig
    
    # 添加论文数据模型（如果存在）
    if has_paper_models:
        models['PaperArticle'] = PaperArticle
        models['PaperMaterialIntermediate'] = PaperMaterialIntermediate
        models['PaperProperty'] = PaperProperty
    
    return models

__all__ = [
    'db',
    'get_models'
]
