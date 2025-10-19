"""
Django Management Command: 初始化知识图谱演示数据
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.knowledge.models import (
    RawMaterial, Intermediate, IntermediateComposition,
    Formula, FormulaComposition, Performance
)
from datetime import date, timedelta
from decimal import Decimal


class Command(BaseCommand):
    help = '初始化材料知识图谱演示数据'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('开始创建材料知识图谱演示数据...'))
        
        # 获取或创建用户
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True}
        )
        if created:
            user.set_password('admin123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'创建管理员用户: {user.username}'))
        
        # 清除旧数据
        self.stdout.write('清理旧数据...')
        Performance.objects.all().delete()
        FormulaComposition.objects.all().delete()
        Formula.objects.all().delete()
        IntermediateComposition.objects.all().delete()
        Intermediate.objects.all().delete()
        RawMaterial.objects.all().delete()
        
        # 创建原材料
        self.stdout.write('\n创建原材料...')
        
        rm1 = RawMaterial.objects.create(
            code='RM-001', name='羟基硅油',
            material_type='polymer', molecular_weight=28000,
            density=0.98, supplier='东岳化工',
            unit_price=Decimal('45.50'), created_by=user
        )
        
        rm2 = RawMaterial.objects.create(
            code='RM-002', name='硅烷偶联剂KH-550',
            material_type='additive', molecular_weight=221.37,
            supplier='南京曙光', unit_price=Decimal('68.00'), created_by=user
        )
        
        rm3 = RawMaterial.objects.create(
            code='RM-003', name='气相二氧化硅',
            material_type='filler', density=2.2,
            supplier='赢创德固赛', unit_price=Decimal('125.00'), created_by=user
        )
        
        rm4 = RawMaterial.objects.create(
            code='RM-004', name='碳酸钙',
            material_type='filler', density=2.71,
            supplier='广西华鑫', unit_price=Decimal('2.80'), created_by=user
        )
        
        rm5 = RawMaterial.objects.create(
            code='RM-005', name='钛酸酯偶联剂',
            material_type='additive', supplier='江苏天禾',
            unit_price=Decimal('85.00'), created_by=user
        )
        
        rm6 = RawMaterial.objects.create(
            code='RM-006', name='甲基三丁酮肟基硅烷',
            material_type='catalyst', molecular_weight=321.52,
            density=0.92, supplier='武汉有机',
            unit_price=Decimal('95.00'), created_by=user
        )
        
        self.stdout.write(self.style.SUCCESS(f'创建了 {RawMaterial.objects.count()} 种原材料'))
        
        # 创建中间体
        self.stdout.write('\n创建中间体...')
        
        int1 = Intermediate.objects.create(
            code='INT-001', name='硅烷封端预聚物A',
            intermediate_type='prepolymer',
            viscosity=8000, solid_content=100,
            created_by=user
        )
        
        IntermediateComposition.objects.create(
            intermediate=int1, raw_material=rm1,
            weight_ratio=85.0, addition_order=1
        )
        IntermediateComposition.objects.create(
            intermediate=int1, raw_material=rm2,
            weight_ratio=15.0, addition_order=2
        )
        
        int2 = Intermediate.objects.create(
            code='INT-002', name='硅油-填料母料B',
            intermediate_type='compound',
            viscosity=12000, solid_content=75,
            created_by=user
        )
        
        IntermediateComposition.objects.create(
            intermediate=int2, raw_material=rm1,
            weight_ratio=60.0, addition_order=1
        )
        IntermediateComposition.objects.create(
            intermediate=int2, raw_material=rm3,
            weight_ratio=10.0, addition_order=2
        )
        IntermediateComposition.objects.create(
            intermediate=int2, raw_material=rm4,
            weight_ratio=28.0, addition_order=3
        )
        IntermediateComposition.objects.create(
            intermediate=int2, raw_material=rm5,
            weight_ratio=2.0, addition_order=4
        )
        
        self.stdout.write(self.style.SUCCESS(f'创建了 {Intermediate.objects.count()} 种中间体'))
        
        # 创建配方
        self.stdout.write('\n创建配方...')
        
        formula1 = Formula.objects.create(
            code='F-2024-001', name='通用型有机硅密封胶',
            version='2.0', status='production',
            application_type='sealant',
            mixing_temperature=25, mixing_time=30,
            curing_temperature=25, curing_time=24,
            created_by=user
        )
        
        FormulaComposition.objects.create(
            formula=formula1, component_type='intermediate',
            intermediate=int1, weight_ratio=45.0, addition_order=1
        )
        FormulaComposition.objects.create(
            formula=formula1, component_type='intermediate',
            intermediate=int2, weight_ratio=50.0, addition_order=2
        )
        FormulaComposition.objects.create(
            formula=formula1, component_type='raw_material',
            raw_material=rm6, weight_ratio=5.0, addition_order=3
        )
        
        formula2 = Formula.objects.create(
            code='F-2024-002', name='高强度有机硅密封胶',
            version='1.5', status='validated',
            application_type='sealant',
            mixing_temperature=25, mixing_time=35,
            curing_temperature=25, curing_time=24,
            created_by=user
        )
        
        FormulaComposition.objects.create(
            formula=formula2, component_type='intermediate',
            intermediate=int1, weight_ratio=60.0, addition_order=1
        )
        FormulaComposition.objects.create(
            formula=formula2, component_type='intermediate',
            intermediate=int2, weight_ratio=35.0, addition_order=2
        )
        FormulaComposition.objects.create(
            formula=formula2, component_type='raw_material',
            raw_material=rm6, weight_ratio=5.0, addition_order=3
        )
        
        self.stdout.write(self.style.SUCCESS(f'创建了 {Formula.objects.count()} 个配方'))
        
        # 创建性能数据
        self.stdout.write('\n创建性能数据...')
        
        Performance.objects.create(
            formula=formula1, test_batch='B20241001',
            test_date=date.today() - timedelta(days=30),
            test_method='GB',
            tensile_strength=1.2, elongation_at_break=450,
            tear_strength=8.5, hardness=25,
            adhesion_strength=0.8, overall_rating=4,
            tested_by=user
        )
        
        Performance.objects.create(
            formula=formula1, test_batch='B20241015',
            test_date=date.today() - timedelta(days=15),
            test_method='GB',
            tensile_strength=1.3, elongation_at_break=480,
            tear_strength=9.0, hardness=26,
            adhesion_strength=0.85, overall_rating=5,
            tested_by=user
        )
        
        Performance.objects.create(
            formula=formula2, test_batch='B20241020',
            test_date=date.today() - timedelta(days=10),
            test_method='GB',
            tensile_strength=1.8, elongation_at_break=380,
            tear_strength=12.0, hardness=32,
            adhesion_strength=1.2, overall_rating=5,
            tested_by=user
        )
        
        self.stdout.write(self.style.SUCCESS(f'创建了 {Performance.objects.count()} 条性能数据'))
        
        # 统计信息
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('数据创建完成！知识图谱统计信息：'))
        self.stdout.write(f'  原材料数量: {RawMaterial.objects.count()}')
        self.stdout.write(f'  中间体数量: {Intermediate.objects.count()}')
        self.stdout.write(f'  配方数量: {Formula.objects.count()}')
        self.stdout.write(f'  性能数据: {Performance.objects.count()}')
        self.stdout.write(f'  中间体组成关系: {IntermediateComposition.objects.count()}')
        self.stdout.write(f'  配方组成关系: {FormulaComposition.objects.count()}')
        self.stdout.write('='*60)
        
        self.stdout.write(self.style.SUCCESS('\n材料知识图谱演示数据创建成功！'))
        self.stdout.write('\n接下来你可以：')
        self.stdout.write('  1. 访问 http://localhost:8000/admin 查看管理后台')
        self.stdout.write('  2. 使用 API: http://localhost:8000/api/kg/ 访问知识图谱API')
        self.stdout.write('  3. 查看完整图谱: GET /api/kg/graph/full_graph/')
