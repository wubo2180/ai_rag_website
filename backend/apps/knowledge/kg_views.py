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


from rest_framework.views import APIView
from apps.documents.models import Document
import pandas as pd
import re
import logging

logger = logging.getLogger(__name__)


class ProcessCSVDocumentsAPIView(APIView):
    """处理CSV文档转知识图谱"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        处理选中的CSV文档，解析材料数据并转换为知识图谱
        """
        document_ids = request.data.get('document_ids', [])
        
        if not document_ids:
            return Response(
                {'error': '请提供文档ID列表'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 获取CSV文档
            documents = Document.objects.filter(
                id__in=document_ids,
                file__iendswith='.csv'
            )
            
            if not documents.exists():
                return Response(
                    {'error': '未找到有效的CSV文档'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            processed_results = []
            
            for doc in documents:
                try:
                    result = self._process_single_csv(doc, request.user)
                    processed_results.append(result)
                except Exception as e:
                    logger.error(f"处理CSV文件 {doc.title} 失败: {str(e)}")
                    processed_results.append({
                        'document_id': doc.id,
                        'document_name': doc.title,
                        'success': False,
                        'error': str(e)
                    })
            
            # 统计结果
            total_processed = len(processed_results)
            successful = sum(1 for r in processed_results if r.get('success', False))
            
            return Response({
                'message': f'处理完成，共处理{total_processed}个文件，成功{successful}个',
                'total_processed': total_processed,
                'successful': successful,
                'results': processed_results
            })
            
        except Exception as e:
            logger.error(f"批量处理CSV文件失败: {str(e)}")
            return Response(
                {'error': f'处理失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _process_single_csv(self, document, user):
        """处理单个CSV文件"""
        import os
        from django.conf import settings
        
        file_path = document.file.path
        
        # 读取CSV文件
        try:
            # 尝试不同的编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                raise ValueError("无法读取CSV文件，编码格式不支持")
            
        except Exception as e:
            raise ValueError(f"读取CSV文件失败: {str(e)}")
        
        # 根据图片中的CSV格式解析数据
        materials_created = []
        intermediates_created = []
        formulas_created = []
        performances_created = []
        
        try:
            with transaction.atomic():
                for index, row in df.iterrows():
                    # 从CSV中提取数据（根据图片中的列结构）
                    material_type = str(row.iloc[0]) if len(row) > 0 and pd.notna(row.iloc[0]) else ""
                    raw_materials = str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else ""
                    intermediate_system = str(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else ""
                    formula_features = str(row.iloc[3]) if len(row) > 3 and pd.notna(row.iloc[3]) else ""
                    performance_indicators = str(row.iloc[4]) if len(row) > 4 and pd.notna(row.iloc[4]) else ""
                    
                    # 跳过空行或无效数据
                    if not material_type or material_type in ['材料类型', 'nan']:
                        continue
                    
                    # 1. 处理原材料
                    if raw_materials:
                        raw_material_names = self._split_materials(raw_materials)
                        for name in raw_material_names:
                            if name.strip():
                                # 如果 user 不是一个持久化 User 实例（例如 AnonymousUser），使用 None
                                created_by_user = user if hasattr(user, 'id') and user.id else None
                                raw_material, created = RawMaterial.objects.get_or_create(
                                    name=name.strip(),
                                    defaults={
                                        'material_type': material_type,
                                        'code': f"RM_{len(materials_created)+1:04d}",
                                        'created_by': created_by_user
                                    }
                                )
                                if created:
                                    materials_created.append(raw_material)
                    
                    # 2. 处理中间体
                    if intermediate_system:
                        intermediate_names = self._split_materials(intermediate_system)
                        for name in intermediate_names:
                            if name.strip():
                                created_by_user = user if hasattr(user, 'id') and user.id else None
                                import uuid
                                unique_code = f"INT_{uuid.uuid4().hex[:8]}"
                                intermediate, created = Intermediate.objects.get_or_create(
                                    name=name.strip(),
                                    defaults={
                                        'code': unique_code,
                                        'description': name.strip(),
                                        'preparation_method': formula_features or "未指定",
                                        'properties': {'composition': name.strip()},
                                        'created_by': created_by_user
                                    }
                                )
                                if created:
                                    intermediates_created.append(intermediate)
                    
                    # 3. 处理配方
                    if formula_features:
                        created_by_user = user if hasattr(user, 'id') and user.id else None
                        import uuid
                        formula_name = f"{material_type}配方_{index+1}"
                        formula_code = f"FML_{uuid.uuid4().hex[:8]}"
                        formula, created = Formula.objects.get_or_create(
                            name=formula_name,
                            defaults={
                                'code': formula_code,
                                'description': formula_features,
                                'properties': {'source_material_type': material_type},
                                'created_by': created_by_user
                            }
                        )
                        if created:
                            formulas_created.append(formula)
                    
                    # 4. 处理性能指标
                    if performance_indicators:
                        performance_data = self._parse_performance(performance_indicators)
                        for perf_data in performance_data:
                            # 如果没有对应的 formula（例如配方未创建），跳过该性能条目
                            target_formula = locals().get('formula', None)
                            if target_formula is None:
                                logger.warning(f"CSV 行 {index+1} 中未找到对应配方，跳过性能创建: {perf_data}")
                                continue

                            # 构建 Performance 的基础字段
                            import datetime
                            created_by_user = user if hasattr(user, 'id') and user.id else None
                            test_batch = (perf_data.get('conditions', '')[:50] or f"batch_{index+1}")
                            test_date = datetime.date.today()
                            test_method = 'other'

                            # 将解析到的性能名称映射到模型字段
                            numeric_fields = {}
                            name_lower = perf_data.get('name', '').lower()
                            try:
                                value_float = float(perf_data.get('value'))
                            except Exception:
                                value_float = None

                            if value_float is not None:
                                if any(k in name_lower for k in ['拉伸', '强度', 'tensile']):
                                    numeric_fields['tensile_strength'] = value_float
                                elif any(k in name_lower for k in ['伸长', 'elongation']):
                                    numeric_fields['elongation_at_break'] = value_float
                                elif any(k in name_lower for k in ['硬度', '硬']):
                                    numeric_fields['hardness'] = value_float
                                elif any(k in name_lower for k in ['密度', 'density']):
                                    numeric_fields['density'] = value_float
                                else:
                                    # 非映射字段保存到 additional_properties
                                    numeric_fields['additional_properties'] = {perf_data.get('name'): perf_data.get('value')}
                            else:
                                numeric_fields['additional_properties'] = {perf_data.get('name'): perf_data.get('value')}

                            perf_kwargs = {
                                'formula': target_formula,
                                'test_batch': test_batch,
                                'test_date': test_date,
                                'test_method': test_method,
                                'test_conditions': perf_data.get('conditions', ''),
                                'tested_by': created_by_user,
                            }
                            perf_kwargs.update(numeric_fields)

                            performance = Performance.objects.create(**perf_kwargs)
                            performances_created.append(performance)
        
        except Exception as e:
            raise ValueError(f"解析CSV数据失败: {str(e)}")
        
        return {
            'document_id': document.id,
            'document_name': document.title,
            'success': True,
            'materials_created': len(materials_created),
            'intermediates_created': len(intermediates_created),
            'formulas_created': len(formulas_created),
            'performances_created': len(performances_created),
            'details': {
                'materials': [m.name for m in materials_created[:5]],  # 只返回前5个
                'intermediates': [i.name for i in intermediates_created[:5]],
                'formulas': [f.name for f in formulas_created[:5]],
                'performances': [p.test_batch for p in performances_created[:5]]
            }
        }
    
    def _split_materials(self, text):
        """分割材料名称，支持多种分隔符"""
        if not text or text.strip() == '':
            return []
        
        # 使用多种分隔符分割
        separators = ['+', '/', '、', '，', ',', '；', ';', '\n']
        materials = [text]
        
        for sep in separators:
            temp = []
            for material in materials:
                temp.extend([m.strip() for m in material.split(sep) if m.strip()])
            materials = temp
        
        return materials
    
    def _parse_performance(self, text):
        """解析性能指标文本"""
        performances = []
        
        if not text or text.strip() == '':
            return performances
        
        # 使用正则表达式提取性能数据
        # 匹配模式如: "热导率1.144 W/(m·K)" 或 "密度<1.5 g/cm³"
        patterns = [
            r'(热导率|密度|硬度|温度|强度)([><!≥≤]?)(\d+\.?\d*)\s*([^\s,，；;]*)',
            r'([^0-9<>!≥≤]+)([><!≥≤]?)(\d+\.?\d*)\s*([^\s,，；;]*)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) >= 3:
                    performances.append({
                        'name': match[0].strip(),
                        'operator': match[1] if len(match) > 1 else '',
                        'value': match[2],
                        'unit': match[3] if len(match) > 3 else '',
                        'conditions': text  # 保存原始文本作为测试条件
                    })
        
        # 如果没有匹配到具体数值，至少保存文本描述
        if not performances:
            performances.append({
                'name': '综合性能',
                'value': '0',
                'unit': '',
                'conditions': text
            })
        
        return performances
