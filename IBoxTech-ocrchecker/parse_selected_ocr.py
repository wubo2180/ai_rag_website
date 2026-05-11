#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
解析选定的论文OCR结果
"""

import json
import sys


def parse_paper_ocr_result():
    """解析论文OCR结果"""
    
    # 用户选择的内容（去掉markdown代码块标记）
    text_content = """{"文献": {"文献编号（Article ID）": "A2", "文献名称（Article Name）": "Soft Composite Gels with High Toughness and Low Thermal Resistance through Lengthening Polymer Strands and Controlling Filler", "四级数据连接（4-level Data Linkage）": [{"原材料（Materials）": {"材料编号（Material ID）": "A2M1", "原材料名称（Material Name）": "氢封端聚二甲基硅氧烷（主链），乙烯基甲基硅氧烷-二甲基硅氧烷共聚物三甲基硅氧基封端PDMS（交联剂），乙烯基封端PDMS（链延长剂）", "CAS号（CAS Number）": ""}, "中间体（Intermediates）": {"中间体编号（Intermediate ID）": "A2I1", "中间体名称（Intermediate Name）": "PDMS聚合物网络"}, "中间体组成（Intermediate Compositions）": "乙烯基与氢基团摩尔比3:2，链延长剂与交联剂比例1:2", "性能（Properties）": [{"性能编号（Property ID）": "A2P1", "性能名称（Property Name）": "断裂能（Fracture Energy） J/m²", "性能值（Property Value）": "4741.48"}, {"性能编号（Property ID）": "A2P2", "性能名称（Property Name）": "拉伸强度（Tensile Strength） kPa", "性能值（Property Value）": "103"}, {"性能编号（Property ID）": "A2P3", "性能名称（Property Name）": "断裂韧性（Fracture Toughness） MJ/m³", "性能值（Property Value）": "1.90"}, {"性能编号（Property ID）": "A2P4", "性能名称（Property Name）": "杨氏模量（Young's Modulus） kPa", "性能值（Property Value）": "340"}, {"性能编号（Property ID）": "A2P5", "性能名称（Property Name）": "伸长率（Elongation at Break）", "性能值（Property Value）": "6.91"}, {"性能编号（Property ID）": "A2P6", "性能名称（Property Name）": "疲劳阈值（Fatigue Threshold） J/m²", "性能值（Property Value）": "723.04"}, {"性能编号（Property ID）": "A2P7", "性能名称（Property Name）": "热阻（Thermal Resistance） cm²·K/W", "性能值（Property Value）": "0.14"}]}, {"原材料（Materials）": {"材料编号（Material ID）": "A2M2", "原材料名称（Material Name）": "球形铝粉，粒径10.0μm", "CAS号（CAS Number）": "7429-90-5"}, "中间体（Intermediates）": {"中间体编号（Intermediate ID）": "A2I2", "中间体名称（Intermediate Name）": "PDMS/铝复合凝胶"}, "中间体组成（Intermediate Compositions）": "铝填料含量80wt%，链延长剂与交联剂比例1:2", "性能（Properties）": [{"性能编号（Property ID）": "A2P8", "性能名称（Property Name）": "粘度（Viscosity） Pa·s", "性能值（Property Value）": "125.0"}, {"性能编号（Property ID）": "A2P9", "性能名称（Property Name）": "热阻（Thermal Resistance） cm²·K/W", "性能值（Property Value）": "0.14"}, {"性能编号（Property ID）": "A2P10", "性能名称（Property Name）": "断裂能（Fracture Energy） J/m²", "性能值（Property Value）": "4741.48"}, {"性能编号（Property ID）": "A2P11", "性能名称（Property Name）": "杨氏模量（Young's Modulus） kPa", "性能值（Property Value）": "340"}, {"性能编号（Property ID）": "A2P12", "性能名称（Property Name）": "伸长率（Elongation at Break）", "性能值（Property Value）": "6.91"}, {"性能编号（Property ID）": "A2P13", "性能名称（Property Name）": "疲劳阈值（Fatigue Threshold） J/m²", "性能值（Property Value）": "723.04"}, {"性能编号（Property ID）": "A2P14", "性能名称（Property Name）": "其他性能（Others）", "性能值（Property Value）": "优异的可加工性和热冲击稳定性"}]}], "性能趋势": "1、增加链延长剂比例可提高聚合物链长度，增强韧性和柔韧性；2、铝填料含量80wt%时达到最佳热阻和力学性能平衡；3、填料含量过高（90wt%）会导致团聚和性能下降"}}"""
    
    print("=" * 100)
    print("📄 论文OCR结果解析")
    print("=" * 100)
    print()
    
    # 解析JSON
    try:
        data = json.loads(text_content)
        print("✅ JSON解析成功")
        print()
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {e}")
        return 1
    
    # 提取文献信息
    if "文献" not in data:
        print("❌ 数据结构错误：缺少'文献'字段")
        return 1
    
    paper = data["文献"]
    
    # 1. 基本信息
    print("-" * 100)
    print("📚 一、文献基本信息")
    print("-" * 100)
    article_id = paper.get("文献编号（Article ID）", "N/A")
    article_name = paper.get("文献名称（Article Name）", "N/A")
    
    print(f"文献编号: {article_id}")
    print(f"文献名称: {article_name}")
    print()
    
    # 2. 性能趋势
    print("-" * 100)
    print("📈 二、性能趋势")
    print("-" * 100)
    trend = paper.get("性能趋势", "")
    if trend:
        trends = trend.split("；")
        for idx, t in enumerate(trends, 1):
            print(f"  {idx}. {t.strip()}")
    else:
        print("  无性能趋势数据")
    print()
    
    # 3. 四级数据连接
    linkage_data = paper.get("四级数据连接（4-level Data Linkage）", [])
    print("-" * 100)
    print(f"🔬 三、四级数据连接 (共 {len(linkage_data)} 组)")
    print("-" * 100)
    print()
    
    total_properties = 0
    
    for idx, item in enumerate(linkage_data, 1):
        print(f"{'=' * 90}")
        print(f"第 {idx} 组数据")
        print(f"{'=' * 90}")
        print()
        
        # 原材料信息
        materials = item.get("原材料（Materials）", {})
        if materials:
            print("  📦 原材料:")
            print(f"    • 材料编号: {materials.get('材料编号（Material ID）', 'N/A')}")
            print(f"    • 材料名称: {materials.get('原材料名称（Material Name）', 'N/A')}")
            cas = materials.get('CAS号（CAS Number）', '')
            print(f"    • CAS号: {cas if cas else '无'}")
            print()
        
        # 中间体信息
        intermediates = item.get("中间体（Intermediates）", {})
        if intermediates:
            print("  🧪 中间体:")
            print(f"    • 中间体编号: {intermediates.get('中间体编号（Intermediate ID）', 'N/A')}")
            print(f"    • 中间体名称: {intermediates.get('中间体名称（Intermediate Name）', 'N/A')}")
            print()
        
        # 中间体组成
        composition = item.get("中间体组成（Intermediate Compositions）", "")
        if composition:
            print("  📊 中间体组成:")
            print(f"    {composition}")
            print()
        
        # 性能数据
        properties = item.get("性能（Properties）", [])
        total_properties += len(properties)
        
        if properties:
            print(f"  ⚡ 性能数据 (共 {len(properties)} 项):")
            print()
            for p_idx, prop in enumerate(properties, 1):
                prop_id = prop.get("性能编号（Property ID）", "N/A")
                prop_name = prop.get("性能名称（Property Name）", "N/A")
                prop_value = prop.get("性能值（Property Value）", "N/A")
                
                print(f"    [{p_idx}] {prop_id}")
                print(f"        名称: {prop_name}")
                print(f"        数值: {prop_value}")
                print()
        else:
            print("  ⚡ 性能数据: 无")
            print()
    
    # 4. 统计信息
    print("=" * 100)
    print("📊 四、统计信息")
    print("=" * 100)
    print(f"总材料/中间体组数: {len(linkage_data)}")
    print(f"总性能数据条数: {total_properties}")
    if len(linkage_data) > 0:
        print(f"平均每组性能数: {total_properties / len(linkage_data):.1f}")
    print()
    
    # 5. 数据库存储结构
    print("=" * 100)
    print("💾 五、数据库存储结构")
    print("=" * 100)
    print()
    print("将会在以下表中创建记录：")
    print()
    print(f"1. paper_articles 表: 1 条记录")
    print(f"   - article_id: {article_id}")
    print(f"   - article_name: {article_name}")
    print(f"   - performance_trend: {trend[:50]}..." if len(trend) > 50 else f"   - performance_trend: {trend}")
    print()
    
    print(f"2. paper_material_intermediates 表: {len(linkage_data)} 条记录")
    for idx, item in enumerate(linkage_data, 1):
        materials = item.get("原材料（Materials）", {})
        intermediates = item.get("中间体（Intermediates）", {})
        mat_id = materials.get('材料编号（Material ID）', 'N/A')
        int_id = intermediates.get('中间体编号（Intermediate ID）', 'N/A')
        print(f"   [{idx}] material_id={mat_id}, intermediate_id={int_id}")
    print()
    
    print(f"3. paper_properties 表: {total_properties} 条记录")
    prop_count = 0
    for item in linkage_data:
        materials = item.get("原材料（Materials）", {})
        mat_id = materials.get('材料编号（Material ID）', 'N/A')
        properties = item.get("性能（Properties）", [])
        for prop in properties:
            prop_count += 1
            prop_id = prop.get("性能编号（Property ID）", "N/A")
            prop_name = prop.get("性能名称（Property Name）", "N/A")
            if prop_count <= 5:  # 只显示前5条
                print(f"   [{prop_count}] property_id={prop_id}, material_id={mat_id}, name={prop_name[:30]}...")
    if total_properties > 5:
        print(f"   ... 还有 {total_properties - 5} 条记录")
    print()
    
    print(f"📊 总计: {1 + len(linkage_data) + total_properties} 条数据库记录")
    print()
    
    # 6. 关键字段映射
    print("=" * 100)
    print("🔑 六、关键字段映射关系")
    print("=" * 100)
    print()
    print("OCR返回字段 → 数据库字段:")
    print()
    print("paper_articles 表:")
    print("  • 文献编号（Article ID） → article_id")
    print("  • 文献名称（Article Name） → article_name")
    print("  • 性能趋势 → performance_trend")
    print()
    print("paper_material_intermediates 表:")
    print("  • 材料编号（Material ID） → material_id")
    print("  • 原材料名称（Material Name） → material_name")
    print("  • CAS号（CAS Number） → cas_number")
    print("  • 中间体编号（Intermediate ID） → intermediate_id")
    print("  • 中间体名称（Intermediate Name） → intermediate_name")
    print("  • 中间体组成（Intermediate Compositions） → intermediate_composition")
    print()
    print("paper_properties 表:")
    print("  • 性能编号（Property ID） → property_id")
    print("  • 性能名称（Property Name） → property_name")
    print("  • 性能值（Property Value） → property_value")
    print()
    
    # 7. 数据结构差异分析
    print("=" * 100)
    print("⚠️  七、数据结构差异")
    print("=" * 100)
    print()
    print("当前OCR结果的数据结构与之前的略有不同：")
    print()
    print("【当前结构】")
    print("  {")
    print("    \"文献\": {")
    print("      \"文献编号（Article ID）\": \"...\",")
    print("      \"四级数据连接（4-level Data Linkage）\": [")
    print("        {")
    print("          \"原材料（Materials）\": {...},")
    print("          \"中间体（Intermediates）\": {...},")
    print("          \"性能（Properties）\": [...]")
    print("        }")
    print("      ]")
    print("    }")
    print("  }")
    print()
    print("【之前期望的结构】")
    print("  {")
    print("    \"文献编号\": \"...\",")
    print("    \"四级数据连接\": [")
    print("      {")
    print("        \"材料编号\": \"...\",")
    print("        \"原材料名称\": \"...\",")
    print("        \"中间体编号\": \"...\",")
    print("        \"性能\": [...]")
    print("      }")
    print("    ]")
    print("  }")
    print()
    print("🔧 建议:")
    print("  1. 需要更新 PaperAdapter 来适配新的嵌套结构")
    print("  2. 字段名称从简单的中文改为了'中文（English）'的双语格式")
    print("  3. 需要从'文献'对象中提取数据，而不是直接从顶层提取")
    print()
    
    print("=" * 100)
    
    return 0


if __name__ == '__main__':
    sys.exit(parse_paper_ocr_result())


