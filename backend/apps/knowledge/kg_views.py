"""
材料知识图谱 API 视图
提供原材料、中间体、配方、性能的CRUD操作和关系查询
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Prefetch
from django.db import transaction
from .models import (
    RawMaterial, Intermediate, IntermediateComposition,
    Formula, FormulaComposition, Performance, KnowledgeGraphRelation
)
from .serializers import (
    RawMaterialSerializer, IntermediateSerializer, IntermediateCompositionSerializer,
    FormulaSerializer, FormulaCompositionSerializer, PerformanceSerializer,
    KnowledgeGraphRelationSerializer, KnowledgeGraphVisualizationSerializer
)


class RawMaterialViewSet(viewsets.ModelViewSet):
    """原材料管理API"""
    queryset = RawMaterial.objects.all()
    serializer_class = RawMaterialSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 过滤参数
        material_type = self.request.query_params.get('material_type')
        search = self.request.query_params.get('search')
        supplier = self.request.query_params.get('supplier')
        
        if material_type:
            queryset = queryset.filter(material_type=material_type)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(chemical_name__icontains=search) |
                Q(cas_number__icontains=search)
            )
        
        if supplier:
            queryset = queryset.filter(supplier__icontains=supplier)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def intermediates(self, request, pk=None):
        """获取使用该原材料的所有中间体"""
        raw_material = self.get_object()
        intermediates = raw_material.intermediates.all()
        serializer = IntermediateSerializer(intermediates, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def usage_chain(self, request, pk=None):
        """获取原材料的完整使用链路（原材料→中间体→配方→性能）"""
        raw_material = self.get_object()
        
        # 查找使用该原材料的中间体
        intermediates = raw_material.intermediates.all()
        
        # 查找使用这些中间体的配方
        formulas = Formula.objects.filter(intermediates__in=intermediates).distinct()
        
        # 查找配方的性能数据
        performances = Performance.objects.filter(formula__in=formulas)
        
        result = {
            'raw_material': RawMaterialSerializer(raw_material).data,
            'intermediates': IntermediateSerializer(intermediates, many=True).data,
            'formulas': FormulaSerializer(formulas, many=True).data,
            'performances': PerformanceSerializer(performances, many=True).data,
        }
        
        return Response(result)


class IntermediateViewSet(viewsets.ModelViewSet):
    """中间体管理API"""
    queryset = Intermediate.objects.prefetch_related('raw_materials').all()
    serializer_class = IntermediateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 过滤参数
        intermediate_type = self.request.query_params.get('intermediate_type')
        search = self.request.query_params.get('search')
        
        if intermediate_type:
            queryset = queryset.filter(intermediate_type=intermediate_type)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search)
            )
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_raw_material(self, request, pk=None):
        """添加原材料到中间体"""
        intermediate = self.get_object()
        serializer = IntermediateCompositionSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(intermediate=intermediate)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def composition(self, request, pk=None):
        """获取中间体的完整组成"""
        intermediate = self.get_object()
        compositions = IntermediateComposition.objects.filter(intermediate=intermediate)
        serializer = IntermediateCompositionSerializer(compositions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def formulas(self, request, pk=None):
        """获取使用该中间体的所有配方"""
        intermediate = self.get_object()
        formulas = intermediate.formulas.all()
        serializer = FormulaSerializer(formulas, many=True)
        return Response(serializer.data)


class FormulaViewSet(viewsets.ModelViewSet):
    """配方管理API"""
    queryset = Formula.objects.prefetch_related('intermediates', 'components').all()
    serializer_class = FormulaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 过滤参数
        status_filter = self.request.query_params.get('status')
        application_type = self.request.query_params.get('application_type')
        search = self.request.query_params.get('search')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if application_type:
            queryset = queryset.filter(application_type=application_type)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search)
            )
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_component(self, request, pk=None):
        """添加组分到配方"""
        formula = self.get_object()
        serializer = FormulaCompositionSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(formula=formula)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def composition(self, request, pk=None):
        """获取配方的完整组成"""
        formula = self.get_object()
        components = formula.components.all()
        serializer = FormulaCompositionSerializer(components, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def performances(self, request, pk=None):
        """获取配方的所有性能数据"""
        formula = self.get_object()
        performances = formula.performances.all()
        serializer = PerformanceSerializer(performances, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def trace_materials(self, request, pk=None):
        """追溯配方的所有原材料来源"""
        formula = self.get_object()
        
        # 获取配方中的所有中间体
        intermediates = formula.intermediates.all()
        
        # 获取所有原材料
        raw_materials = set()
        for intermediate in intermediates:
            raw_materials.update(intermediate.raw_materials.all())
        
        # 也包括直接添加的原材料
        direct_raw_materials = RawMaterial.objects.filter(
            id__in=formula.components.filter(
                component_type='raw_material'
            ).values_list('raw_material_id', flat=True)
        )
        raw_materials.update(direct_raw_materials)
        
        result = {
            'formula': FormulaSerializer(formula).data,
            'intermediates': IntermediateSerializer(intermediates, many=True).data,
            'raw_materials': RawMaterialSerializer(list(raw_materials), many=True).data,
        }
        
        return Response(result)
    
    @action(detail=False, methods=['post'])
    def recommend(self, request):
        """基于性能要求推荐配方"""
        # 获取性能要求
        required_tensile_strength = request.data.get('tensile_strength_min')
        required_elongation = request.data.get('elongation_min')
        required_hardness = request.data.get('hardness_max')
        application_type = request.data.get('application_type')
        
        # 查询满足条件的配方
        formulas = Formula.objects.filter(status='validated')
        
        if application_type:
            formulas = formulas.filter(application_type=application_type)
        
        # 根据性能筛选
        if required_tensile_strength:
            formulas = formulas.filter(
                performances__tensile_strength__gte=required_tensile_strength
            )
        
        if required_elongation:
            formulas = formulas.filter(
                performances__elongation_at_break__gte=required_elongation
            )
        
        if required_hardness:
            formulas = formulas.filter(
                performances__hardness__lte=required_hardness
            )
        
        formulas = formulas.distinct()
        serializer = FormulaSerializer(formulas, many=True)
        
        return Response({
            'count': formulas.count(),
            'formulas': serializer.data
        })


class PerformanceViewSet(viewsets.ModelViewSet):
    """性能数据管理API"""
    queryset = Performance.objects.select_related('formula').all()
    serializer_class = PerformanceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 过滤参数
        formula_id = self.request.query_params.get('formula')
        test_method = self.request.query_params.get('test_method')
        rating_min = self.request.query_params.get('rating_min')
        
        if formula_id:
            queryset = queryset.filter(formula_id=formula_id)
        
        if test_method:
            queryset = queryset.filter(test_method=test_method)
        
        if rating_min:
            queryset = queryset.filter(overall_rating__gte=rating_min)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(tested_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取性能数据统计"""
        from django.db.models import Avg, Max, Min, Count
        
        formula_id = request.query_params.get('formula')
        queryset = self.get_queryset()
        
        if formula_id:
            queryset = queryset.filter(formula_id=formula_id)
        
        stats = queryset.aggregate(
            avg_tensile_strength=Avg('tensile_strength'),
            max_tensile_strength=Max('tensile_strength'),
            min_tensile_strength=Min('tensile_strength'),
            avg_elongation=Avg('elongation_at_break'),
            avg_hardness=Avg('hardness'),
            avg_rating=Avg('overall_rating'),
            total_tests=Count('id')
        )
        
        return Response(stats)


class KnowledgeGraphViewSet(viewsets.ViewSet):
    """知识图谱综合查询API"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def full_graph(self, request):
        """获取完整知识图谱数据（用于可视化）"""
        # 获取所有实体
        raw_materials = RawMaterial.objects.all()
        intermediates = Intermediate.objects.prefetch_related('raw_materials').all()
        formulas = Formula.objects.prefetch_related('intermediates').all()
        performances = Performance.objects.select_related('formula').all()
        
        # 构建节点
        nodes = []
        edges = []
        
        # 原材料节点
        for rm in raw_materials:
            nodes.append({
                'id': f'rm_{rm.id}',
                'name': rm.name,
                'type': 'raw_material',
                'category': 0,
                'symbolSize': 30,
                'data': {
                    'code': rm.code,
                    'material_type': rm.get_material_type_display(),
                    'supplier': rm.supplier,
                }
            })
        
        # 中间体节点和边
        for intermediate in intermediates:
            nodes.append({
                'id': f'int_{intermediate.id}',
                'name': intermediate.name,
                'type': 'intermediate',
                'category': 1,
                'symbolSize': 40,
                'data': {
                    'code': intermediate.code,
                    'intermediate_type': intermediate.get_intermediate_type_display(),
                }
            })
            
            # 原材料→中间体关系
            for comp in intermediate.intermediatecomposition_set.all():
                edges.append({
                    'source': f'rm_{comp.raw_material_id}',
                    'target': f'int_{intermediate.id}',
                    'value': comp.weight_ratio,
                    'label': f'{comp.weight_ratio}%'
                })
        
        # 配方节点和边
        for formula in formulas:
            nodes.append({
                'id': f'formula_{formula.id}',
                'name': formula.name,
                'type': 'formula',
                'category': 2,
                'symbolSize': 50,
                'data': {
                    'code': formula.code,
                    'version': formula.version,
                    'status': formula.get_status_display(),
                    'application_type': formula.get_application_type_display(),
                }
            })
            
            # 中间体→配方关系
            for comp in formula.components.filter(component_type='intermediate'):
                if comp.intermediate:
                    edges.append({
                        'source': f'int_{comp.intermediate_id}',
                        'target': f'formula_{formula.id}',
                        'value': comp.weight_ratio,
                        'label': f'{comp.weight_ratio}%'
                    })
        
        # 性能节点和边
        for perf in performances:
            nodes.append({
                'id': f'perf_{perf.id}',
                'name': f'性能-{perf.test_batch}',
                'type': 'performance',
                'category': 3,
                'symbolSize': 35,
                'data': {
                    'test_date': str(perf.test_date),
                    'tensile_strength': perf.tensile_strength,
                    'elongation': perf.elongation_at_break,
                    'hardness': perf.hardness,
                    'rating': perf.overall_rating,
                }
            })
            
            # 配方→性能关系
            edges.append({
                'source': f'formula_{perf.formula_id}',
                'target': f'perf_{perf.id}',
                'value': perf.overall_rating or 3,
                'label': f'评分{perf.overall_rating or "N/A"}'
            })
        
        result = {
            'nodes': nodes,
            'edges': edges,
            'categories': [
                {'name': '原材料'},
                {'name': '中间体'},
                {'name': '配方'},
                {'name': '性能'},
            ],
            'stats': {
                'raw_materials_count': len(raw_materials),
                'intermediates_count': len(intermediates),
                'formulas_count': len(formulas),
                'performances_count': len(performances),
            }
        }
        
        return Response(result)
    
    @action(detail=False, methods=['post'])
    def search_path(self, request):
        """搜索从原材料到性能的完整路径"""
        raw_material_id = request.data.get('raw_material_id')
        target_performance = request.data.get('target_performance')  # 如tensile_strength >= 2.0
        
        if not raw_material_id:
            return Response(
                {'error': '请提供原材料ID'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 查找路径
        raw_material = RawMaterial.objects.get(id=raw_material_id)
        paths = []
        
        # 原材料→中间体
        for intermediate in raw_material.intermediates.all():
            # 中间体→配方
            for formula in intermediate.formulas.all():
                # 配方→性能
                performances = formula.performances.all()
                
                # 根据性能要求过滤
                if target_performance:
                    # 这里可以添加更复杂的性能筛选逻辑
                    pass
                
                for perf in performances:
                    paths.append({
                        'raw_material': RawMaterialSerializer(raw_material).data,
                        'intermediate': IntermediateSerializer(intermediate).data,
                        'formula': FormulaSerializer(formula).data,
                        'performance': PerformanceSerializer(perf).data,
                    })
        
        return Response({
            'count': len(paths),
            'paths': paths
        })
