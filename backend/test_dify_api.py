"""
测试 Dify API 连接和请求格式
"""
import requests
import json
import re

# Dify 配置
API_KEY = "app-2WflAIBZKQGLwUImUXbYaLsN"
BASE_URL = "http://172.20.46.18:8088/v1"

def analyze_markdown_content(text):
    """分析文本内容是否为Markdown格式"""
    print(f"\n🔍 详细Markdown格式分析:")
    print("=" * 50)
    
    # Markdown特征检查
    markdown_features = {
        '标题 (# ## ###)': [r'^#{1,6}\s+.+$', 'multiline'],
        '粗体 (**text** __text__)': [r'\*\*[^*]+\*\*|__[^_]+__', 'single'],
        '斜体 (*text* _text_)': [r'\*[^*]+\*|_[^_]+_', 'single'], 
        '代码块 (```)': [r'```[\s\S]*?```', 'single'],
        '行内代码 (`)': [r'`[^`]+`', 'single'],
        '无序列表 (- * +)': [r'^[\s]*[-\*\+]\s+.+$', 'multiline'],
        '有序列表 (1. 2.)': [r'^[\s]*\d+\.\s+.+$', 'multiline'],
        '链接 [text](url)': [r'\[([^\]]+)\]\(([^)]+)\)', 'single'],
        '图片 ![alt](url)': [r'!\[([^\]]*)\]\(([^)]+)\)', 'single'],
        '引用 (>)': [r'^[\s]*>\s+.+$', 'multiline'],
        '分割线 (---)': [r'^[\s]*[-_*]{3,}[\s]*$', 'multiline'],
        '表格 (|)': [r'^[\s]*\|.*\|[\s]*$', 'multiline'],
    }
    
    found_features = []
    
    for feature_name, (pattern, mode) in markdown_features.items():
        if mode == 'multiline':
            matches = re.findall(pattern, text, re.MULTILINE)
        else:
            matches = re.findall(pattern, text)
            
        if matches:
            found_features.append(feature_name)
            print(f"   ✅ {feature_name}")
            # 显示前3个匹配示例
            for i, match in enumerate(matches[:3]):
                if isinstance(match, tuple):
                    match = match[0] if match else str(match)
                match_str = str(match).strip()[:50]
                if len(str(match).strip()) > 50:
                    match_str += "..."
                print(f"      示例{i+1}: {match_str}")
            if len(matches) > 3:
                print(f"      ... 还有 {len(matches)-3} 个匹配")
        else:
            print(f"   ❌ {feature_name}")
    
    # 整体评估
    print(f"\n📊 Markdown评估结果:")
    if len(found_features) >= 3:
        print(f"   🎉 这是标准的Markdown格式文本!")
        print(f"   📝 发现了 {len(found_features)} 种Markdown特征")
    elif len(found_features) >= 1:
        print(f"   📝 这是轻度Markdown格式文本")
        print(f"   🔍 发现了 {len(found_features)} 种Markdown特征")
    else:
        print(f"   📄 这是纯文本格式")
        print(f"   ℹ️  未发现Markdown格式特征")
    
    return len(found_features)

def test_markdown_output():
    """专门测试Markdown输出格式"""
    print("\n" + "="*60)
    print("🎯 专门测试Markdown输出格式")
    print("="*60)
    
    url = f"{BASE_URL}/chat-messages"
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # 使用更可能产生Markdown格式的问题
    test_queries = [
        "Python有哪些数据类型？"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 测试 {i}: {query}")
        print("-" * 50)
        
        payload = {
            'inputs': {
                'largeModel': '通义千问'
            },
            'query': query,
            'response_mode': 'blocking',
            'user': 'test_user'
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                response_data = response.json()
                if 'answer' in response_data:
                    answer_text = response_data['answer']
                    print(f"📤 原始输出:")
                    print(f"{answer_text}")
                    analyze_markdown_content(answer_text)
                else:
                    print("⚠️  响应中未找到 'answer' 字段")
            else:
                print(f"❌ 请求失败，状态码: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求错误: {str(e)}")
        except Exception as e:
            print(f"❌ 其他错误: {str(e)}")
        
        if i < len(test_queries):
            print("\n" + "-"*30)

def test_dify_api():
    """测试 Dify API"""
    url = f"{BASE_URL}/chat-messages"
    
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # 测试1: 最简单的请求
    print("=" * 50)
    print("测试1: 最简单的请求（不带模型参数）")
    print("=" * 50)
    
    payload1 = {
        'query': '你好',
        'response_mode': 'blocking',
        'user': 'test_user'
    }
    
    print(f"\n请求 URL: {url}")
    print(f"请求头: {json.dumps(headers, indent=2, ensure_ascii=False)}")
    print(f"请求体: {json.dumps(payload1, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=payload1, headers=headers, timeout=30)
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 请求错误: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"错误详情: {e.response.text}")
    except Exception as e:
        print(f"\n❌ 其他错误: {str(e)}")
    
    # 测试2: 带 inputs.largeModel 参数
    print("\n" + "=" * 50)
    print("测试2: 带 inputs.largeModel 参数")
    print("=" * 50)
    
    payload2 = {
        'inputs': {
            'largeModel': '通义千问'
        },
        'query': '你好',
        'response_mode': 'blocking',
        'user': 'test_user'
    }
    
    print(f"\n请求 URL: {url}")
    print(f"请求体: {json.dumps(payload2, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=payload2, headers=headers, timeout=30)
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"完整响应内容: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            
            # 提取并分析文本内容
            if 'answer' in response_data:
                answer_text = response_data['answer']
                print(f"\n📝 提取的回答文本:")
                print("-" * 40)
                print(answer_text)
                print("-" * 40)
                
                # 检查是否为Markdown格式
                print(f"\n🔍 Markdown格式检查:")
                markdown_indicators = {
                    '标题': ['#', '##', '###'],
                    '粗体': ['**', '__'],
                    '斜体': ['*', '_'],
                    '代码块': ['```', '`'],
                    '列表': ['- ', '* ', '1. ', '2. '],
                    '链接': ['[', ']('],
                    '换行': ['\n'],
                }
                
                found_markdown = False
                for feature, indicators in markdown_indicators.items():
                    for indicator in indicators:
                        if indicator in answer_text:
                            print(f"   ✅ 发现 {feature} 标记: '{indicator}'")
                            found_markdown = True
                            break
                
                if not found_markdown:
                    print("   ℹ️  未发现明显的Markdown标记，可能是纯文本")
                else:
                    print("   🎉 内容包含Markdown格式!")
                
                # 分析文本结构
                lines = answer_text.split('\n')
                print(f"\n📊 文本结构分析:")
                print(f"   - 总行数: {len(lines)}")
                print(f"   - 总字符数: {len(answer_text)}")
                print(f"   - 包含空行: {'是' if '' in lines else '否'}")
                
            else:
                print("⚠️  响应中未找到 'answer' 字段")
        else:
            print(f"响应内容: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 请求错误: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"错误详情: {e.response.text}")
    except Exception as e:
        print(f"\n❌ 其他错误: {str(e)}")
    
    # 测试3: 带 inputs 但不带 largeModel
    print("\n" + "=" * 50)
    print("测试3: 带空的 inputs 对象")
    print("=" * 50)
    
    payload3 = {
        'inputs': {},
        'query': '你好',
        'response_mode': 'blocking',
        'user': 'test_user'
    }
    
    print(f"\n请求 URL: {url}")
    print(f"请求体: {json.dumps(payload3, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=payload3, headers=headers, timeout=30)
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 请求错误: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"错误详情: {e.response.text}")
    except Exception as e:
        print(f"\n❌ 其他错误: {str(e)}")
    
    # 测试4: 检查 API 参数工作流配置
    print("\n" + "=" * 50)
    print("提示：如果所有测试都失败，可能的原因：")
    print("=" * 50)
    print("1. Dify 工作流未启动或未正确配置")
    print("2. API 密钥不正确")
    print("3. 工作流中的变量名称不匹配")
    print("4. 需要在 Dify 工作流中配置必填参数")
    print("\n请检查 Dify 后台的工作流配置：")
    print("- 打开 Dify 后台: http://localhost")
    print("- 进入对应的应用")
    print("- 检查 API 访问 -> 查看 API 文档")
    print("- 确认必填参数和可选参数")

if __name__ == '__main__':
    # 先运行原始测试
    test_dify_api()
    
    # 然后运行专门的Markdown格式测试
    test_markdown_output()
