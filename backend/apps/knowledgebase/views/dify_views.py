"""
Dify 知识库管理 API 视图
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import requests
import json


class DifyDatasetListAPIView(APIView):
    """获取Dify知识库列表"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """获取知识库列表"""
        try:
            # 获取查询参数
            keyword = request.GET.get('keyword', '')
            page = int(request.GET.get('page', 1))
            limit = int(request.GET.get('limit', 20))
            tag_ids = request.GET.getlist('tag_ids')

            # 构建API请求 - 使用正确的Dify API配置
            base_url = getattr(settings, 'DIFY_DATASET_BASE_URL')
            api_key = getattr(settings, 'DIFY_DATASET_API_KEY')
            
            # 确保base_url正确：如果已经包含datasets路径，直接使用；否则拼接
            if base_url.endswith('/datasets'):
                url = base_url
            else:
                url = f"{base_url}/datasets"
            headers = {
                'Authorization': f'Bearer {api_key}'
            }
            
            # 构建查询参数
            querystring = {
                'page': str(page),
                'limit': str(limit)
            }
            
            if keyword:
                querystring['keyword'] = keyword
            if tag_ids:
                querystring['tag_ids'] = tag_ids

            print(f"🔍 请求Dify知识库列表: {url}")
            print(f"📋 查询参数: {querystring}")

            # 发送请求
            response = requests.get(url, headers=headers, params=querystring, timeout=30)
            
            print(f"📡 Dify API响应状态: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ 成功获取知识库列表，共 {data.get('total', 0)} 个知识库")
                
                # 处理数据格式，添加一些辅助信息
                datasets = data.get('data', [])
                for dataset in datasets:
                    # 计算创建时间的可读格式
                    if 'created_at' in dataset:
                        try:
                            from datetime import datetime
                            dataset['created_at_readable'] = datetime.fromtimestamp(
                                dataset['created_at']
                            ).strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            dataset['created_at_readable'] = '未知'
                    
                    # 添加状态信息
                    dataset['status'] = '可用' if dataset.get('embedding_available', False) else '处理中'
                
                return Response({
                    'success': True,
                    'data': data,
                    'message': f'成功获取 {len(datasets)} 个知识库'
                })
            
            else:
                error_msg = f"Dify API错误 ({response.status_code})"
                try:
                    error_data = response.json()
                    error_msg += f": {error_data.get('message', response.text)}"
                except:
                    error_msg += f": {response.text}"
                
                print(f"❌ {error_msg}")
                return Response({
                    'success': False,
                    'error': error_msg,
                    'data': {'data': [], 'total': 0, 'page': page, 'limit': limit}
                }, status=status.HTTP_400_BAD_REQUEST)

        except requests.exceptions.Timeout:
            error_msg = "请求超时，请检查网络连接"
            print(f"⏰ {error_msg}")
            return Response({
                'success': False,
                'error': error_msg,
                'data': {'data': [], 'total': 0, 'page': 1, 'limit': 20}
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
            
        except Exception as e:
            error_msg = f"获取知识库列表失败: {str(e)}"
            print(f"💥 {error_msg}")
            return Response({
                'success': False,
                'error': error_msg,
                'data': {'data': [], 'total': 0, 'page': 1, 'limit': 20}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DifyDatasetDetailAPIView(APIView):
    """获取知识库详情"""
    permission_classes = [IsAuthenticated]

    def get(self, request, dataset_id):
        """获取指定知识库的详情"""
        try:
            base_url = getattr(settings, 'DIFY_DATASET_BASE_URL')
            api_key = getattr(settings, 'DIFY_DATASET_API_KEY')

            # 确保URL正确拼接
            if base_url.endswith('/datasets'):
                url = f"{base_url}/{dataset_id}"
            else:
                url = f"{base_url}/datasets/{dataset_id}"
            headers = {
                'Authorization': f'Bearer {api_key}'
            }

            print(f"🔍 请求知识库详情: {url}")

            response = requests.get(url, headers=headers, timeout=30)
            
            print(f"📡 Dify API响应状态: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ 成功获取知识库详情: {data.get('name', '未知')}")
                
                return Response({
                    'success': True,
                    'data': data,
                    'message': '成功获取知识库详情'
                })
            
            else:
                error_msg = f"Dify API错误 ({response.status_code})"
                try:
                    error_data = response.json()
                    error_msg += f": {error_data.get('message', response.text)}"
                except:
                    error_msg += f": {response.text}"
                
                print(f"❌ {error_msg}")
                return Response({
                    'success': False,
                    'error': error_msg
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            error_msg = f"获取知识库详情失败: {str(e)}"
            print(f"💥 {error_msg}")
            return Response({
                'success': False,
                'error': error_msg
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DifyDatasetDocumentsAPIView(APIView):
    """获取知识库文档列表"""
    permission_classes = [IsAuthenticated]

    def get(self, request, dataset_id):
        """获取指定知识库的文档列表"""
        try:
            # 获取查询参数
            keyword = request.GET.get('keyword', '')
            page = int(request.GET.get('page', 1))
            limit = int(request.GET.get('limit', 20))

            base_url = getattr(settings, 'DIFY_DATASET_BASE_URL')
            api_key = getattr(settings, 'DIFY_DATASET_API_KEY')

            # 确保URL正确拼接
            if base_url.endswith('/datasets'):
                url = f"{base_url}/{dataset_id}/documents"
            else:
                url = f"{base_url}/datasets/{dataset_id}/documents"
            headers = {
                'Authorization': f'Bearer {api_key}'
            }
            
            # 构建查询参数
            querystring = {
                'page': str(page),
                'limit': str(limit)
            }
            
            if keyword:
                querystring['keyword'] = keyword

            print(f"🔍 请求知识库文档列表: {url}")
            print(f"📋 查询参数: {querystring}")

            response = requests.get(url, headers=headers, params=querystring, timeout=30)
            
            print(f"📡 Dify API响应状态: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                documents = data.get('data', [])
                print(f"✅ 成功获取文档列表，共 {len(documents)} 个文档")
                
                return Response({
                    'success': True,
                    'data': data,
                    'message': f'成功获取 {len(documents)} 个文档'
                })
            
            else:
                error_msg = f"Dify API错误 ({response.status_code})"
                try:
                    error_data = response.json()
                    error_msg += f": {error_data.get('message', response.text)}"
                except:
                    error_msg += f": {response.text}"
                
                print(f"❌ {error_msg}")
                return Response({
                    'success': False,
                    'error': error_msg,
                    'data': {'data': [], 'total': 0, 'page': page, 'limit': limit}
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            error_msg = f"获取文档列表失败: {str(e)}"
            print(f"💥 {error_msg}")
            return Response({
                'success': False,
                'error': error_msg,
                'data': {'data': [], 'total': 0, 'page': 1, 'limit': 20}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)