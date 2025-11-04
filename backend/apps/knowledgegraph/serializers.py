"""
材料知识图谱序列化器
"""
from rest_framework import serializers
from .models import (
    RawMaterial, Intermediate, IntermediateComposition,
    Formula, FormulaComposition, Performance, KnowledgeGraphRelation
)


class RawMaterialSerializer(serializers.ModelSerializer):
    """原材料序列化器"""
    material_type_display = serializers.CharField(source='get_material_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = RawMaterial
        fields = [
            'id', 'code', 'name', 'chemical_name', 'cas_number',
            'material_type', 'material_type_display',
            'molecular_formula', 'molecular_weight', 'density', 'viscosity',
            'supplier', 'unit_price',
            'properties', 'description',
            'created_at', 'updated_at', 'created_by', 'created_by_name'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by']


class IntermediateCompositionSerializer(serializers.ModelSerializer):
    """中间体组成序列化器"""
    raw_material_name = serializers.CharField(source='raw_material.name', read_only=True)
    raw_material_code = serializers.CharField(source='raw_material.code', read_only=True)
    
    class Meta:
        model = IntermediateComposition
        fields = [
            'id', 'intermediate', 'raw_material', 
            'raw_material_name', 'raw_material_code',
            'weight_ratio', 'addition_order', 
            'addition_temperature', 'addition_notes'
        ]


class IntermediateSerializer(serializers.ModelSerializer):
    """中间体序列化器"""
    intermediate_type_display = serializers.CharField(source='get_intermediate_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    composition = IntermediateCompositionSerializer(source='intermediatecomposition_set', many=True, read_only=True)
    raw_materials_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Intermediate
        fields = [
            'id', 'code', 'name', 'intermediate_type', 'intermediate_type_display',
            'preparation_method', 'reaction_conditions',
            'viscosity', 'solid_content',
            'properties', 'description',
            'raw_materials_count', 'composition',
            'created_at', 'updated_at', 'created_by', 'created_by_name'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by']
    
    def get_raw_materials_count(self, obj):
        return obj.raw_materials.count()


class FormulaCompositionSerializer(serializers.ModelSerializer):
    """配方组成序列化器"""
    component_name = serializers.SerializerMethodField()
    component_code = serializers.SerializerMethodField()
    component_type_display = serializers.CharField(source='get_component_type_display', read_only=True)
    
    class Meta:
        model = FormulaComposition
        fields = [
            'id', 'formula', 'component_type', 'component_type_display',
            'intermediate', 'raw_material',
            'component_name', 'component_code',
            'weight_ratio', 'addition_order', 'addition_notes'
        ]
    
    def get_component_name(self, obj):
        if obj.intermediate:
            return obj.intermediate.name
        elif obj.raw_material:
            return obj.raw_material.name
        return None
    
    def get_component_code(self, obj):
        if obj.intermediate:
            return obj.intermediate.code
        elif obj.raw_material:
            return obj.raw_material.code
        return None


class PerformanceSerializer(serializers.ModelSerializer):
    """性能数据序列化器"""
    formula_name = serializers.CharField(source='formula.name', read_only=True)
    formula_code = serializers.CharField(source='formula.code', read_only=True)
    test_method_display = serializers.CharField(source='get_test_method_display', read_only=True)
    tested_by_name = serializers.CharField(source='tested_by.username', read_only=True)
    
    class Meta:
        model = Performance
        fields = [
            'id', 'formula', 'formula_name', 'formula_code',
            'test_batch', 'test_date', 'test_method', 'test_method_display',
            'test_conditions',
            # 力学性能
            'tensile_strength', 'elongation_at_break', 'tear_strength', 'hardness',
            # 粘接性能
            'adhesion_strength',
            # 耐候性能
            'weather_resistance', 'water_resistance',
            # 热性能
            'heat_resistance_temp', 'cold_resistance_temp',
            # 其他性能
            'viscosity', 'density', 'tack_free_time', 'full_cure_time',
            # 扩展和评价
            'additional_properties', 'overall_rating', 'notes',
            'created_at', 'updated_at', 'tested_by', 'tested_by_name'
        ]
        read_only_fields = ['created_at', 'updated_at', 'tested_by']


class FormulaSerializer(serializers.ModelSerializer):
    """配方序列化器"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    application_type_display = serializers.CharField(source='get_application_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    composition = FormulaCompositionSerializer(source='components', many=True, read_only=True)
    latest_performance = serializers.SerializerMethodField()
    intermediates_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Formula
        fields = [
            'id', 'code', 'name', 'version', 
            'status', 'status_display',
            'application_type', 'application_type_display',
            # 工艺参数
            'mixing_temperature', 'mixing_time',
            'curing_temperature', 'curing_time',
            # 描述
            'process_description', 'precautions',
            'properties', 'description',
            # 关联信息
            'intermediates_count', 'composition', 'latest_performance',
            'created_at', 'updated_at', 'created_by', 'created_by_name'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by']
    
    def get_latest_performance(self, obj):
        latest = obj.performances.order_by('-test_date').first()
        if latest:
            return {
                'test_date': latest.test_date,
                'tensile_strength': latest.tensile_strength,
                'elongation_at_break': latest.elongation_at_break,
                'hardness': latest.hardness,
                'overall_rating': latest.overall_rating,
            }
        return None
    
    def get_intermediates_count(self, obj):
        return obj.intermediates.count()


class KnowledgeGraphRelationSerializer(serializers.ModelSerializer):
    """知识图谱关系序列化器"""
    relation_type_display = serializers.CharField(source='get_relation_type_display', read_only=True)
    
    class Meta:
        model = KnowledgeGraphRelation
        fields = [
            'id', 'relation_type', 'relation_type_display',
            'source_type', 'source_id', 'source_name',
            'target_type', 'target_id', 'target_name',
            'weight', 'properties',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class KnowledgeGraphVisualizationSerializer(serializers.Serializer):
    """知识图谱可视化数据序列化器"""
    nodes = serializers.ListField(
        child=serializers.DictField(),
        help_text="图谱节点列表"
    )
    edges = serializers.ListField(
        child=serializers.DictField(),
        help_text="图谱边列表"
    )
    categories = serializers.ListField(
        child=serializers.DictField(),
        help_text="节点分类"
    )
    stats = serializers.DictField(
        help_text="统计信息"
    )
