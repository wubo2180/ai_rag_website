"""
材料知识图谱示例数据初始化脚本
生成原材料→中间体→配方→性能的完整数据链
"""
import os
import django
import sys
from datetime import date, timedelta
from decimal import Decimal

# 设置Django环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from apps.knowledgegraph.models import (
    RawMaterial, Intermediate, IntermediateComposition,
    Formula, FormulaComposition, Performance
)


def create_demo_data():
    """创建演示数据"""
    
    print("🚀 开始创建材料知识图谱演示数据...")
    
    # 获取或创建用户
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True}
    )
    if created:
        user.set_password('admin123')
        user.save()
        print(f"✅ 创建管理员用户: {user.username}")
    
    # 清除旧数据（可选）
    print("🧹 清理旧数据...")
    Performance.objects.all().delete()
    FormulaComposition.objects.all().delete()
    Formula.objects.all().delete()
    IntermediateComposition.objects.all().delete()
    Intermediate.objects.all().delete()
    RawMaterial.objects.all().delete()
    
    # ==================== 第一级：原材料 ====================
    print("\n📦 创建原材料...")
    
    raw_materials = [
        {
            'code': 'RM-001',
            'name': '羟基硅油',
            'chemical_name': '羟基封端聚二甲基硅氧烷',
            'cas_number': '70131-67-8',
            'material_type': 'polymer',
            'molecular_weight': 28000,
            'density': 0.98,
            'viscosity': 5000,
            'supplier': '东岳化工',
            'unit_price': Decimal('45.50'),
            'description': '主要成膜物质，提供基本的力学性能'
        },
        {
            'code': 'RM-002',
            'name': '硅烷偶联剂KH-550',
            'chemical_name': '3-氨丙基三乙氧基硅烷',
            'cas_number': '919-30-2',
            'material_type': 'additive',
            'molecular_weight': 221.37,
            'density': 0.946,
            'supplier': '南京曙光',
            'unit_price': Decimal('68.00'),
            'description': '增强粘接性能，改善与基材的结合力'
        },
        {
            'code': 'RM-003',
            'name': '气相二氧化硅',
            'chemical_name': '纳米二氧化硅',
            'cas_number': '112945-52-5',
            'material_type': 'filler',
            'density': 2.2,
            'supplier': '赢创德固赛',
            'unit_price': Decimal('125.00'),
            'description': '补强填料，提高强度和耐候性'
        },
        {
            'code': 'RM-004',
            'name': '碳酸钙',
            'chemical_name': '轻质碳酸钙',
            'cas_number': '471-34-1',
            'material_type': 'filler',
            'molecular_weight': 100.09,
            'density': 2.71,
            'supplier': '广西华鑫',
            'unit_price': Decimal('2.80'),
            'description': '填充剂，降低成本，改善流变性'
        },
        {
            'code': 'RM-005',
            'name': '钛酸酯偶联剂',
            'chemical_name': '异丙基三异硬脂酰钛酸酯',
            'cas_number': '61417-49-0',
            'material_type': 'additive',
            'supplier': '江苏天禾',
            'unit_price': Decimal('85.00'),
            'description': '改善填料分散，增强界面结合'
        },
        {
            'code': 'RM-006',
            'name': '甲基三丁酮肟基硅烷',
            'chemical_name': 'MTBOS',
            'cas_number': '22984-54-9',
            'material_type': 'catalyst',
            'molecular_weight': 321.52,
            'density': 0.92,
            'supplier': '武汉有机',
            'unit_price': Decimal('95.00'),
            'description': '交联剂，控制固化速度'
        },
    ]
    
    created_raw_materials = {}
    for data in raw_materials:
        rm = RawMaterial.objects.create(**data, created_by=user)
        created_raw_materials[data['code']] = rm
        print(f"  ✓ {rm.code} - {rm.name}")
    
    # ==================== 第二级：中间体 ====================
    print("\n🧪 创建中间体...")
    
    # 中间体1：预聚物A
    int1 = Intermediate.objects.create(
        code='INT-001',
        name='硅烷封端预聚物A',
        intermediate_type='prepolymer',
        preparation_method='在80-90℃下，将羟基硅油与硅烷偶联剂KH-550反应2-3小时',
        reaction_conditions={
            'temperature': '80-90℃',
            'time': '2-3h',
            'catalyst': '二月桂酸二丁基锡'
        },
        viscosity=8000,
        solid_content=100,
        description='具有优异粘接性能的预聚物',
        created_by=user
    )
    
    # 添加组成
    IntermediateComposition.objects.create(
        intermediate=int1,
        raw_material=created_raw_materials['RM-001'],
        weight_ratio=85.0,
        addition_order=1,
        addition_temperature=25,
        addition_notes='先加入羟基硅油'
    )
    IntermediateComposition.objects.create(
        intermediate=int1,
        raw_material=created_raw_materials['RM-002'],
        weight_ratio=15.0,
        addition_order=2,
        addition_temperature=80,
        addition_notes='升温后缓慢加入硅烷偶联剂'
    )
    print(f"  ✓ {int1.code} - {int1.name} (2种原材料)")
    
    # 中间体2：填料母料B
    int2 = Intermediate.objects.create(
        code='INT-002',
        name='硅油-填料母料B',
        intermediate_type='compound',
        preparation_method='在高速分散机中将羟基硅油与气相二氧化硅和碳酸钙混合分散',
        reaction_conditions={
            'temperature': '常温',
            'time': '1-2h',
            'speed': '2000rpm'
        },
        viscosity=12000,
        solid_content=75,
        description='高分散性填料母料',
        created_by=user
    )
    
    IntermediateComposition.objects.create(
        intermediate=int2,
        raw_material=created_raw_materials['RM-001'],
        weight_ratio=60.0,
        addition_order=1,
        addition_notes='先加入硅油作为分散介质'
    )
    IntermediateComposition.objects.create(
        intermediate=int2,
        raw_material=created_raw_materials['RM-003'],
        weight_ratio=10.0,
        addition_order=2,
        addition_notes='分批加入气相二氧化硅'
    )
    IntermediateComposition.objects.create(
        intermediate=int2,
        raw_material=created_raw_materials['RM-004'],
        weight_ratio=28.0,
        addition_order=3,
        addition_notes='最后加入碳酸钙'
    )
    IntermediateComposition.objects.create(
        intermediate=int2,
        raw_material=created_raw_materials['RM-005'],
        weight_ratio=2.0,
        addition_order=4,
        addition_notes='添加偶联剂改善分散'
    )
    print(f"  ✓ {int2.code} - {int2.name} (4种原材料)")
    
    # ==================== 第三级：配方 ====================
    print("\n📋 创建配方...")
    
    # 配方1：通用型密封胶
    formula1 = Formula.objects.create(
        code='F-2024-001',
        name='通用型有机硅密封胶',
        version='2.0',
        status='production',
        application_type='sealant',
        mixing_temperature=25,
        mixing_time=30,
        curing_temperature=25,
        curing_time=24,
        process_description='''
1. 将预聚物A加入行星搅拌机中
2. 加入填料母料B，混合均匀
3. 抽真空脱气10分钟
4. 加入交联剂MTBOS，快速混合
5. 包装密封
        ''',
        precautions='操作过程中避免水分进入，交联剂需最后添加',
        description='适用于建筑门窗、幕墙等密封应用',
        created_by=user
    )
    
    # 添加配方组成
    FormulaComposition.objects.create(
        formula=formula1,
        component_type='intermediate',
        intermediate=int1,
        weight_ratio=45.0,
        addition_order=1,
        addition_notes='主要成膜组分'
    )
    FormulaComposition.objects.create(
        formula=formula1,
        component_type='intermediate',
        intermediate=int2,
        weight_ratio=50.0,
        addition_order=2,
        addition_notes='填料组分'
    )
    FormulaComposition.objects.create(
        formula=formula1,
        component_type='raw_material',
        raw_material=created_raw_materials['RM-006'],
        weight_ratio=5.0,
        addition_order=3,
        addition_notes='交联剂，最后添加'
    )
    print(f"  ✓ {formula1.code} - {formula1.name}")
    
    # 配方2：高强度密封胶
    formula2 = Formula.objects.create(
        code='F-2024-002',
        name='高强度有机硅密封胶',
        version='1.5',
        status='validated',
        application_type='sealant',
        mixing_temperature=25,
        mixing_time=35,
        curing_temperature=25,
        curing_time=24,
        process_description='与通用型相似，但增加预聚物比例',
        description='适用于结构密封和高强度粘接',
        created_by=user
    )
    
    FormulaComposition.objects.create(
        formula=formula2,
        component_type='intermediate',
        intermediate=int1,
        weight_ratio=60.0,
        addition_order=1
    )
    FormulaComposition.objects.create(
        formula=formula2,
        component_type='intermediate',
        intermediate=int2,
        weight_ratio=35.0,
        addition_order=2
    )
    FormulaComposition.objects.create(
        formula=formula2,
        component_type='raw_material',
        raw_material=created_raw_materials['RM-006'],
        weight_ratio=5.0,
        addition_order=3
    )
    print(f"  ✓ {formula2.code} - {formula2.name}")
    
    # ==================== 第四级：性能数据 ====================
    print("\n📊 创建性能数据...")
    
    # 配方1的性能数据
    perf1_1 = Performance.objects.create(
        formula=formula1,
        test_batch='B20241001',
        test_date=date.today() - timedelta(days=30),
        test_method='GB',
        test_conditions={'temperature': '23±2℃', 'humidity': '50±5%'},
        tensile_strength=1.2,
        elongation_at_break=450,
        tear_strength=8.5,
        hardness=25,
        adhesion_strength=0.8,
        weather_resistance='优秀',
        water_resistance='良好',
        heat_resistance_temp=150,
        cold_resistance_temp=-40,
        viscosity=15000,
        density=1.02,
        tack_free_time=0.5,
        full_cure_time=24,
        overall_rating=4,
        notes='性能稳定，符合GB/T 14683标准',
        tested_by=user
    )
    
    perf1_2 = Performance.objects.create(
        formula=formula1,
        test_batch='B20241015',
        test_date=date.today() - timedelta(days=15),
        test_method='GB',
        test_conditions={'temperature': '23±2℃', 'humidity': '50±5%'},
        tensile_strength=1.3,
        elongation_at_break=480,
        tear_strength=9.0,
        hardness=26,
        adhesion_strength=0.85,
        weather_resistance='优秀',
        water_resistance='良好',
        heat_resistance_temp=150,
        cold_resistance_temp=-40,
        viscosity=14500,
        density=1.03,
        tack_free_time=0.45,
        full_cure_time=22,
        overall_rating=5,
        notes='性能提升，批次稳定性好',
        tested_by=user
    )
    print(f"  ✓ {formula1.name} - 2个测试批次")
    
    # 配方2的性能数据
    perf2_1 = Performance.objects.create(
        formula=formula2,
        test_batch='B20241020',
        test_date=date.today() - timedelta(days=10),
        test_method='GB',
        test_conditions={'temperature': '23±2℃', 'humidity': '50±5%'},
        tensile_strength=1.8,
        elongation_at_break=380,
        tear_strength=12.0,
        hardness=32,
        adhesion_strength=1.2,
        weather_resistance='优秀',
        water_resistance='优秀',
        heat_resistance_temp=160,
        cold_resistance_temp=-45,
        viscosity=18000,
        density=1.05,
        tack_free_time=0.6,
        full_cure_time=24,
        overall_rating=5,
        notes='高强度配方，各项指标优异',
        tested_by=user
    )
    print(f"  ✓ {formula2.name} - 1个测试批次")
    
    # 统计信息
    print("\n" + "="*60)
    print("✨ 数据创建完成！知识图谱统计信息：")
    print(f"  📦 原材料数量: {RawMaterial.objects.count()}")
    print(f"  🧪 中间体数量: {Intermediate.objects.count()}")
    print(f"  📋 配方数量: {Formula.objects.count()}")
    print(f"  📊 性能数据: {Performance.objects.count()}")
    print(f"  🔗 中间体组成关系: {IntermediateComposition.objects.count()}")
    print(f"  🔗 配方组成关系: {FormulaComposition.objects.count()}")
    print("="*60)
    
    print("\n🎉 材料知识图谱演示数据创建成功！")
    print("\n💡 接下来你可以：")
    print("  1. 访问 http://localhost:8000/admin 查看管理后台")
    print("  2. 使用 API: http://localhost:8000/api/kg/ 访问知识图谱API")
    print("  3. 查看完整图谱: GET /api/kg/graph/full_graph/")
    print("  4. 搜索路径: POST /api/kg/graph/search_path/")
    print("  5. 推荐配方: POST /api/kg/formulas/recommend/")


if __name__ == '__main__':
    create_demo_data()
