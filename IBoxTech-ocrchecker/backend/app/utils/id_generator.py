"""
ID生成器工具
用于生成各种格式的唯一ID
"""
import random
import string
from typing import Set


class IDGenerator:
    """ID生成器类"""
    
    @staticmethod
    def generate_article_id() -> str:
        """
        生成文献编号
        格式: A-XXXXX （A- + 5位随机字符串，包含数字和字母）
        
        Returns:
            str: 文献编号，例如 "A-3K7M9"
        """
        # 生成5位随机字符串（数字+大写字母）
        chars = string.ascii_uppercase + string.digits  # A-Z, 0-9
        random_str = ''.join(random.choices(chars, k=5))
        return f"A-{random_str}"
    
    @staticmethod
    def check_article_id_uniqueness(article_id: str, existing_ids: Set[str]) -> bool:
        """
        检查文献编号是否唯一
        
        Args:
            article_id: 待检查的文献编号
            existing_ids: 已存在的文献编号集合
            
        Returns:
            bool: 如果唯一返回True，否则返回False
        """
        return article_id not in existing_ids
    
    @staticmethod
    def generate_unique_article_id(existing_ids: Set[str], max_attempts: int = 100) -> str:
        """
        生成唯一的文献编号（确保不重复）
        
        Args:
            existing_ids: 已存在的文献编号集合
            max_attempts: 最大尝试次数
            
        Returns:
            str: 唯一的文献编号
            
        Raises:
            RuntimeError: 如果超过最大尝试次数仍无法生成唯一ID
        """
        for _ in range(max_attempts):
            article_id = IDGenerator.generate_article_id()
            if IDGenerator.check_article_id_uniqueness(article_id, existing_ids):
                return article_id
        
        raise RuntimeError(f"无法生成唯一的文献编号（尝试了{max_attempts}次）")
    
    @staticmethod
    def generate_material_id(article_id: str, sequence: int) -> str:
        """
        生成材料编号
        格式: 文献编号:M{序号} （例如 "A-3K7M9:M1"）
        
        Args:
            article_id: 文献编号
            sequence: 序号（从1开始）
            
        Returns:
            str: 材料编号
        """
        return f"{article_id}:M{sequence}"
    
    @staticmethod
    def generate_intermediate_id(article_id: str, sequence: int) -> str:
        """
        生成中间体编号
        格式: 文献编号:I{序号} （例如 "A-3K7M9:I1"）
        
        Args:
            article_id: 文献编号
            sequence: 序号（从1开始）
            
        Returns:
            str: 中间体编号
        """
        return f"{article_id}:I{sequence}"
    
    @staticmethod
    def generate_property_id(article_id: str, sequence: int) -> str:
        """
        生成性能编号
        格式: 文献编号:P{序号} （例如 "A-3K7M9:P1"）
        
        Args:
            article_id: 文献编号
            sequence: 序号（从1开始）
            
        Returns:
            str: 性能编号
        """
        return f"{article_id}:P{sequence}"


def get_existing_article_ids_from_db() -> Set[str]:
    """
    从数据库获取所有已存在的文献编号
    
    Returns:
        Set[str]: 文献编号集合
    """
    from models import get_models
    
    models = get_models()
    PaperArticle = models['PaperArticle']
    
    # 查询所有文献编号
    existing_articles = PaperArticle.query.with_entities(PaperArticle.article_id).all()
    existing_ids = {article.article_id for article in existing_articles if article.article_id}
    
    return existing_ids


