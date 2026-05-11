#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import sys

# 测试获取文件详情API
def test_get_file_detail(file_id, token):
    url = f'http://localhost:5000/api/files/{file_id}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    print(f"测试URL: {url}")
    print(f"Token: {token[:50]}..." if len(token) > 50 else f"Token: {token}")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"\n状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python test_api.py <file_id> <token>")
        print("\n从浏览器控制台获取token:")
        print("localStorage.getItem('access_token')")
        sys.exit(1)
    
    file_id = sys.argv[1]
    token = sys.argv[2]
    test_get_file_detail(file_id, token)
