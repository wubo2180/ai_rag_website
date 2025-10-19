from django.contrib import admin
from .models import (
    Knowledge, RawMaterial, Intermediate, IntermediateComposition,
    Formula, FormulaComposition, Performance, KnowledgeGraphRelation
)

@admin.register(Knowledge)
class KnowledgeAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'updated_at')
    search_fields = ('title', 'content')
    list_filter = ('created_at', 'updated_at')


# ==================== 材料知识图谱管理 ====================

class IntermediateCompositionInline(admin.TabularInline):
    """中间体组成内联"""
    model = IntermediateComposition
    extra = 1
    fields = ['raw_material', 'weight_ratio', 'addition_order', 'addition_temperature']


class FormulaCompositionInline(admin.TabularInline):
    """配方组成内联"""
    model = FormulaComposition
    extra = 1
    fields = ['component_type', 'intermediate', 'raw_material', 'weight_ratio', 'addition_order']


@admin.register(RawMaterial)
class RawMaterialAdmin(admin.ModelAdmin):
    """原材料管理"""
    list_display = ['code', 'name', 'material_type', 'supplier', 'unit_price', 'created_at']
    list_filter = ['material_type', 'supplier', 'created_at']
    search_fields = ['code', 'name', 'chemical_name', 'cas_number']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('基本信息', {
            'fields': ('code', 'name', 'chemical_name', 'cas_number', 'material_type')
        }),
        ('物理化学性质', {
            'fields': ('molecular_formula', 'molecular_weight', 'density', 'viscosity')
        }),
        ('供应商信息', {
            'fields': ('supplier', 'unit_price')
        }),
        ('其他信息', {
            'fields': ('properties', 'description', 'created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(Intermediate)
class IntermediateAdmin(admin.ModelAdmin):
    """中间体管理"""
    list_display = ['code', 'name', 'intermediate_type', 'viscosity', 'solid_content', 'created_at']
    list_filter = ['intermediate_type', 'created_at']
    search_fields = ['code', 'name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [IntermediateCompositionInline]
    fieldsets = (
        ('基本信息', {
            'fields': ('code', 'name', 'intermediate_type')
        }),
        ('制备信息', {
            'fields': ('preparation_method', 'reaction_conditions')
        }),
        ('性质', {
            'fields': ('viscosity', 'solid_content')
        }),
        ('其他信息', {
            'fields': ('properties', 'description', 'created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(Formula)
class FormulaAdmin(admin.ModelAdmin):
    """配方管理"""
    list_display = ['code', 'name', 'version', 'status', 'application_type', 'created_at']
    list_filter = ['status', 'application_type', 'created_at']
    search_fields = ['code', 'name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [FormulaCompositionInline]
    fieldsets = (
        ('基本信息', {
            'fields': ('code', 'name', 'version', 'status', 'application_type')
        }),
        ('工艺参数', {
            'fields': ('mixing_temperature', 'mixing_time', 'curing_temperature', 'curing_time')
        }),
        ('工艺描述', {
            'fields': ('process_description', 'precautions')
        }),
        ('其他信息', {
            'fields': ('properties', 'description', 'created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(Performance)
class PerformanceAdmin(admin.ModelAdmin):
    """性能数据管理"""
    list_display = ['formula', 'test_batch', 'test_date', 'test_method', 'overall_rating']
    list_filter = ['test_method', 'test_date', 'overall_rating']
    search_fields = ['formula__name', 'formula__code', 'test_batch']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('测试信息', {
            'fields': ('formula', 'test_batch', 'test_date', 'test_method', 'test_conditions')
        }),
        ('力学性能', {
            'fields': ('tensile_strength', 'elongation_at_break', 'tear_strength', 'hardness')
        }),
        ('粘接性能', {
            'fields': ('adhesion_strength',)
        }),
        ('耐候性能', {
            'fields': ('weather_resistance', 'water_resistance')
        }),
        ('热性能', {
            'fields': ('heat_resistance_temp', 'cold_resistance_temp')
        }),
        ('其他性能', {
            'fields': ('viscosity', 'density', 'tack_free_time', 'full_cure_time')
        }),
        ('评价', {
            'fields': ('additional_properties', 'overall_rating', 'notes', 'tested_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(KnowledgeGraphRelation)
class KnowledgeGraphRelationAdmin(admin.ModelAdmin):
    """知识图谱关系管理"""
    list_display = ['relation_type', 'source_name', 'target_name', 'weight', 'created_at']
    list_filter = ['relation_type', 'source_type', 'target_type']
    search_fields = ['source_name', 'target_name']
    readonly_fields = ['created_at', 'updated_at']