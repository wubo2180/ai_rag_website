"""
完整的CSV转知识图谱功能测试和演示
"""
import os
import sys
import django
import pandas as pd

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from apps.documents.models import Document, DocumentCategory, DocumentFolder
from apps.knowledge.models import RawMaterial, Intermediate, Formula, Performance
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction

def create_sample_csv_document():
    """创建示例CSV文档"""
    print("📄 创建示例CSV文档...")
    
    try:
        # 获取或创建用户
        user, created = User.objects.get_or_create(
            username='test_user',
            defaults={'email': 'test@example.com', 'first_name': '测试', 'last_name': '用户'}
        )
        
        # 获取或创建分类
        category, created = DocumentCategory.objects.get_or_create(
            name='材料数据',
            defaults={'color': '#409eff', 'created_by': user}
        )
        
        # 读取示例CSV文件
        csv_path = 'sample_materials.csv'
        if not os.path.exists(csv_path):
            print(f"❌ 找不到文件: {csv_path}")
            return None
        
        with open(csv_path, 'rb') as f:
            csv_content = f.read()
        
        # 创建文档对象
        uploaded_file = SimpleUploadedFile(
            name='材料知识图谱数据.csv',
            content=csv_content,
            content_type='text/csv'
        )
        
        # 检查是否已存在
        existing_doc = Document.objects.filter(
            title='材料知识图谱数据.csv',
            uploaded_by=user
        ).first()
        
        if existing_doc:
            print(f"✅ 使用已存在的文档: {existing_doc.title} (ID: {existing_doc.id})")
            return existing_doc
        
        # 创建新文档
        document = Document.objects.create(
            title='材料知识图谱数据.csv',
            file=uploaded_file,
            category=category,
            uploaded_by=user,
            file_size=len(csv_content)
        )
        
        print(f"✅ 创建文档成功: {document.title} (ID: {document.id})")
        return document
        
    except Exception as e:
        print(f"❌ 创建文档失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def process_csv_manually(document):
    """手动处理CSV文件（简化版本）"""
    print(f"\n🔄 手动处理CSV文件: {document.title}")
    
    try:
        # 获取用户
        user = document.uploaded_by
        
        # 读取CSV文件
        df = pd.read_csv(document.file.path, encoding='utf-8')
        print(f"📊 CSV文件包含 {len(df)} 行数据")
        print(f"📋 列名: {list(df.columns)}")
        
        results = {
            'materials_created': 0,
            'intermediates_created': 0,
            'formulas_created': 0,
            'performances_created': 0
        }
        
        with transaction.atomic():
            for index, row in df.iterrows():
                print(f"\n处理第 {index + 1} 行数据...")
                
                # 提取数据
                material_type = str(row.iloc[0]) if len(row) > 0 and pd.notna(row.iloc[0]) else ""
                raw_materials = str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else ""
                intermediate_system = str(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else ""
                formula_features = str(row.iloc[3]) if len(row) > 3 and pd.notna(row.iloc[3]) else ""
                performance_indicators = str(row.iloc[4]) if len(row) > 4 and pd.notna(row.iloc[4]) else ""
                
                print(f"  材料类型: {material_type}")
                print(f"  原材料: {raw_materials}")
                print(f"  中间体: {intermediate_system}")
                print(f"  配方特征: {formula_features}")
                print(f"  性能指标: {performance_indicators}")
                
                # 跳过无效行
                if not material_type or material_type in ['材料类型', 'nan']:
                    continue
                
                # 1. 处理原材料
                if raw_materials and raw_materials != 'nan':
                    raw_material_names = split_materials(raw_materials)
                    for name in raw_material_names:
                        if name.strip():
                            raw_material, created = RawMaterial.objects.get_or_create(
                                name=name.strip(),
                                defaults={
                                    'material_type': 'polymer',  # 默认类型
                                    'code': f"RM_{results['materials_created']+1:04d}",
                                    'created_by': user
                                }
                            )
                            if created:
                                results['materials_created'] += 1
                                print(f"    ✅ 创建原材料: {name.strip()}")
                
                # 2. 处理中间体
                if intermediate_system and intermediate_system != 'nan':
                    intermediate_names = split_materials(intermediate_system)
                    for name in intermediate_names:
                        if name.strip():
                            intermediate, created = Intermediate.objects.get_or_create(
                                name=name.strip(),
                                defaults={
                                    'code': f"INT_{results['intermediates_created']+1:04d}",
                                    'intermediate_type': 'compound',
                                    'preparation_method': formula_features or "未指定",
                                    'created_by': user
                                }
                            )
                            if created:
                                results['intermediates_created'] += 1
                                print(f"    ✅ 创建中间体: {name.strip()}")
                
                # 3. 处理配方
                if formula_features and formula_features != 'nan':
                    formula_name = f"{material_type}配方_{str(index+1)}" if material_type != 'nan' else f"配方_{str(index+1)}"
                    formula, created = Formula.objects.get_or_create(
                        name=formula_name,
                        defaults={
                            'code': f"F_{results['formulas_created']+1:04d}",
                            'version': '1.0',
                            'application_type': 'thermal',  # 默认为导热应用
                            'description': formula_features,
                            'created_by': user
                        }
                    )
                    if created:
                        results['formulas_created'] += 1
                        print(f"    ✅ 创建配方: {formula_name}")
                
                # 4. 处理性能指标
                if performance_indicators and performance_indicators != 'nan' and 'formula' in locals() and formula:
                    performance_data = parse_performance(performance_indicators)
                    
                    # 创建基本性能记录
                    from datetime import datetime
                    performance, created = Performance.objects.get_or_create(
                        formula=formula,
                        test_batch=f"Batch_{results['performances_created']+1:03d}",
                        defaults={
                            'test_date': datetime.now().date(),
                            'test_method': 'CSV导入',
                            'test_conditions': performance_indicators,
                            'notes': f"从CSV导入: {performance_indicators}",
                            'tested_by': user
                        }
                    )
                    
                    if created:
                        # 解析具体的性能数值并更新
                        for perf_data in performance_data:
                            name = perf_data['name'].lower()
                            value = float(perf_data['value']) if perf_data['value'].replace('.', '').isdigit() else None
                            
                            # 根据性能名称映射到具体字段
                            if '热导率' in name or 'thermal' in name:
                                # 存储到additional_properties中
                                if performance.additional_properties is None:
                                    performance.additional_properties = {}
                                performance.additional_properties['thermal_conductivity'] = {
                                    'value': perf_data['value'],
                                    'unit': perf_data['unit'],
                                    'operator': perf_data.get('operator', '')
                                }
                            elif '密度' in name or 'density' in name:
                                if value:
                                    performance.density = value
                            elif '硬度' in name or 'hardness' in name:
                                if value:
                                    performance.hardness = value
                        
                        performance.save()
                        results['performances_created'] += 1
                        print(f"    ✅ 创建性能指标: {formula.name}")
        
        print(f"\n✅ 处理完成!")
        print(f"📊 统计结果:")
        print(f"  - 原材料: {results['materials_created']} 个")
        print(f"  - 中间体: {results['intermediates_created']} 个")
        print(f"  - 配方: {results['formulas_created']} 个")
        print(f"  - 性能指标: {results['performances_created']} 个")
        
        return results
        
    except Exception as e:
        print(f"❌ 处理失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def split_materials(text):
    """分割材料名称"""
    if not text or text.strip() == '' or text == 'nan':
        return []
    
    separators = ['+', '/', '、', '，', ',', '；', ';', '\n']
    materials = [text]
    
    for sep in separators:
        temp = []
        for material in materials:
            temp.extend([m.strip() for m in material.split(sep) if m.strip() and m.strip() != 'nan'])
        materials = temp
    
    return materials

def parse_performance(text):
    """解析性能指标"""
    import re
    
    performances = []
    
    if not text or text.strip() == '' or text == 'nan':
        return performances
    
    # 简化的性能解析
    # 分割多个性能指标
    segments = text.replace('，', ',').split(',')
    
    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue
        
        # 尝试提取数值和单位
        match = re.search(r'([\u4e00-\u9fa5]+)([><!≥≤]?)(\d+\.?\d*)\s*([^\s,，；;]*)', segment)
        
        if match:
            performances.append({
                'name': match.group(1).strip(),
                'operator': match.group(2) if match.group(2) else '',
                'value': match.group(3),
                'unit': match.group(4) if match.group(4) else '',
                'conditions': text
            })
        else:
            # 如果无法解析数值，保存为描述性指标
            performances.append({
                'name': segment[:20],  # 取前20个字符作为名称
                'value': '0',
                'unit': '',
                'conditions': text
            })
    
    if not performances:
        performances.append({
            'name': '综合性能',
            'value': '0',
            'unit': '',
            'conditions': text
        })
    
    return performances

def check_knowledge_graph_data():
    """检查知识图谱数据"""
    print("\n📊 检查知识图谱数据...")
    
    materials_count = RawMaterial.objects.count()
    intermediates_count = Intermediate.objects.count()
    formulas_count = Formula.objects.count()
    performances_count = Performance.objects.count()
    
    print(f"  - 原材料数量: {materials_count}")
    print(f"  - 中间体数量: {intermediates_count}")
    print(f"  - 配方数量: {formulas_count}")
    print(f"  - 性能指标数量: {performances_count}")
    
    # 显示一些示例数据
    if materials_count > 0:
        print(f"\n原材料示例:")
        for material in RawMaterial.objects.all()[:3]:
            print(f"  - {material.name} ({material.code})")
    
    if intermediates_count > 0:
        print(f"\n中间体示例:")
        for intermediate in Intermediate.objects.all()[:3]:
            print(f"  - {intermediate.name}")
    
    if formulas_count > 0:
        print(f"\n配方示例:")
        for formula in Formula.objects.all()[:3]:
            print(f"  - {formula.name}: {formula.description[:50]}...")

def main():
    print("🚀 CSV转知识图谱功能测试")
    print("=" * 60)
    
    # 1. 创建示例CSV文档
    document = create_sample_csv_document()
    if not document:
        return
    
    # 2. 处理CSV文件
    results = process_csv_manually(document)
    if not results:
        return
    
    # 3. 检查结果
    check_knowledge_graph_data()
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("💡 提示: 现在可以在前端页面测试文件选择和转换功能了")

if __name__ == '__main__':
    main()