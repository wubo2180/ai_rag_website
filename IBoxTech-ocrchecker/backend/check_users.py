#!/usr/bin/env python3
"""检查数据库中的用户数据"""
from models import db
from models.user import User
from app import create_app

app = create_app()

with app.app_context():
    users = User.query.all()
    print(f'用户总数: {len(users)}')
    print('-' * 60)
    for u in users:
        print(f'ID: {u.id}')
        print(f'用户名: {u.username}')
        print(f'邮箱: {u.email}')
        print(f'真实姓名: {u.real_name or "未设置"}')
        print(f'角色: {u.role}')
        print(f'状态: {"激活" if u.is_active else "禁用"}')
        print(f'最后登录: {u.last_login_at or "从未登录"}')
        print(f'创建时间: {u.created_at}')
        print('-' * 60)

