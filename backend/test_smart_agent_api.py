"""
智能体API测试脚本
"""
import requests
import json
from pprint import pprint

# API基础URL
BASE_URL = "http://127.0.0.1:8000/api"

# 测试用户认证（使用Django的会话认证）
session = requests.Session()

def test_agents_list():
    """测试获取智能体列表"""
    print("=" * 50)
    print("测试智能体列表API")
    print("=" * 50)
    
    response = session.get(f"{BASE_URL}/smart-agent/agents/")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        agents = response.json()
        print(f"智能体数量: {len(agents)}")
        
        if agents:
            print("\n智能体列表:")
            for agent in agents:
                print(f"- {agent['display_name']} ({agent['category']})")
                print(f"  描述: {agent['description'][:100]}...")
                print(f"  状态: {agent['status']}, 评分: {agent['popularity_score']}")
                print()
        return agents
    else:
        print(f"请求失败: {response.text}")
        return []

def test_agent_categories():
    """测试获取智能体分类"""
    print("=" * 50)
    print("测试智能体分类API")
    print("=" * 50)
    
    response = session.get(f"{BASE_URL}/smart-agent/agents/categories/")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        categories = response.json()
        print("智能体分类统计:")
        pprint(categories)
        return categories
    else:
        print(f"请求失败: {response.text}")
        return []

def test_execute_agent(agent_id, task_data):
    """测试执行智能体任务"""
    print("=" * 50)
    print(f"测试执行智能体任务 - Agent ID: {agent_id}")
    print("=" * 50)
    
    response = session.post(
        f"{BASE_URL}/smart-agent/agents/{agent_id}/execute/",
        json=task_data,
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code in [200, 201]:
        result = response.json()
        print("执行结果:")
        pprint(result)
        return result
    else:
        print(f"请求失败: {response.text}")
        return None

def test_agent_statistics(agent_id):
    """测试获取智能体统计信息"""
    print("=" * 50)
    print(f"测试智能体统计信息 - Agent ID: {agent_id}")
    print("=" * 50)
    
    response = session.get(f"{BASE_URL}/smart-agent/agents/{agent_id}/statistics/")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        stats = response.json()
        print("统计信息:")
        pprint(stats)
        return stats
    else:
        print(f"请求失败: {response.text}")
        return None

def run_comprehensive_test():
    """运行综合测试"""
    print("🚀 开始智能体模块API测试")
    print("=" * 80)
    
    # 1. 测试智能体列表
    agents = test_agents_list()
    
    # 2. 测试分类统计
    categories = test_agent_categories()
    
    if not agents:
        print("❌ 没有可用的智能体，测试终止")
        return
    
    # 3. 选择第一个智能体进行详细测试
    first_agent = agents[0]
    agent_id = first_agent['id']
    
    print(f"选择智能体: {first_agent['display_name']} 进行测试")
    
    # 4. 测试执行任务
    if first_agent['category'] == 'data_analysis':
        task_data = {
            "title": "材料数据链分析测试",
            "description": "测试四级关联数据链生成功能",
            "input_data": {
                "material_composition": {
                    "Fe": 85.5,
                    "C": 0.45,
                    "Mn": 0.8,
                    "Si": 0.3,
                    "P": 0.025,
                    "S": 0.015
                },
                "process_parameters": {
                    "temperature": 1200,
                    "pressure": 150,
                    "cooling_rate": 5,
                    "duration": 120
                },
                "test_conditions": {
                    "temperature": 25,
                    "humidity": 45
                }
            }
        }
    elif first_agent['category'] == 'property_prediction':
        task_data = {
            "title": "材料性质预测测试",
            "description": "测试化学性质预测功能",
            "input_data": {
                "molecular_formula": "Fe-0.45C-0.8Mn",
                "crystal_structure": "BCC",
                "composition": {
                    "Fe": 85.5,
                    "C": 0.45,
                    "Mn": 0.8
                }
            }
        }
    else:
        task_data = {
            "title": "通用智能体测试",
            "description": "测试智能体基础功能",
            "input_data": {
                "test_data": "这是一个测试数据",
                "parameters": {"param1": "value1", "param2": "value2"}
            }
        }
    
    # 执行任务
    result = test_execute_agent(agent_id, task_data)
    
    # 5. 测试统计信息
    test_agent_statistics(agent_id)
    
    print("\n" + "=" * 80)
    print("🎉 测试完成！")

if __name__ == "__main__":
    try:
        run_comprehensive_test()
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保Django服务器正在运行")
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()