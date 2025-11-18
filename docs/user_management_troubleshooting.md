# 用户管理功能排查清单

## 问题诊断

前端调用 `/api/auth/users/` 返回 404

## 修复内容

### 1. ✅ 后端权限类 (`backend/apps/accounts/permissions.py`)

- 新增 `IsProfileAdmin` 权限类
- 检查 `UserProfile.role == 'ADMIN'` 而不是 Django 的 `is_staff`

### 2. ✅ 后端 API 视图 (`backend/apps/accounts/api_views.py`)

更新以下视图的权限类为 `IsProfileAdmin`：

- `UserListAPIView` (获取用户列表)
- `DepartmentDetailAPIView` (部门详情)
- `UserRoleDepartmentUpdateAPIView` (分配角色)

### 3. ✅ 前端 API 调用 (`frontend/src/views/UserManagement.vue`)

- 使用 `apiClient` 替代 `axios`
- 移除硬编码的 API_BASE URL
- API 路径：
  - `/auth/users/` - 获取用户列表
  - `/auth/departments/` - 获取部门列表
  - `/auth/users/assign-role/` - 分配角色
  - `/auth/departments/` - 创建部门

### 4. ✅ 前端用户状态管理 (`frontend/src/stores/user.js`)

- 登录/注册后自动调用 `fetchUserInfo()` 获取完整的 profile 数据
- `user.value` 包含 `profile.role` 信息

### 5. ✅ 前端导航栏 (`frontend/src/components/Navigation.vue`)

- 添加"用户管理"按钮
- 使用 `isAdmin` 计算属性判断是否显示（检查 `user.profile.role === 'ADMIN'`）

## 需要检查的事项

### 检查后端服务

```bash
# 确认后端服务在 8080 端口运行
netstat -an | grep 8080
# 或
curl http://127.0.0.1:8080/api/test/
```

### 检查用户角色

需要确保至少有一个用户的 `profile.role` 设置为 `'ADMIN'`

方法一：使用 Django Admin

1. 访问 http://127.0.0.1:8080/admin/
2. 找到 User profiles
3. 编辑用户，设置 role 为 "ADMIN"

方法二：使用 Django Shell（需要激活虚拟环境）

```python
python manage.py shell
from apps.accounts.models import User, UserProfile
user = User.objects.get(username='your_username')
profile, created = UserProfile.objects.get_or_create(user=user)
profile.role = 'ADMIN'
profile.save()
# 同步 is_staff
user.is_staff = True
user.save()
```

### 前端测试步骤

1. 启动前端开发服务器：`npm run dev`（在 frontend 目录）
2. 访问 http://localhost:3000
3. 使用管理员账号登录
4. 检查导航栏是否显示"用户管理"按钮
5. 点击按钮，查看是否能正常访问用户管理页面
6. 打开浏览器开发者工具 -> Network 标签，查看 API 请求

### 常见错误及解决方案

**404 Not Found**

- 检查后端服务是否运行
- 检查 URL 路径是否正确（注意尾部斜杠）
- 检查前端代理配置 (`vite.config.js`)

**403 Forbidden**

- 用户没有管理员权限（`profile.role != 'ADMIN'`）
- Token 过期或无效
- 检查请求头是否包含正确的 Authorization

**401 Unauthorized**

- 未登录或 token 无效
- 检查 localStorage 中是否有 `access_token`

## API 端点总结

### 用户相关

- `GET /api/auth/users/` - 获取所有用户（需要 ADMIN）
- `POST /api/auth/users/assign-role/` - 分配角色/部门（需要 ADMIN）
- `GET /api/auth/user-info/` - 获取当前用户信息（需要认证）

### 部门相关

- `GET /api/auth/departments/` - 获取部门列表（认证用户可读）
- `POST /api/auth/departments/` - 创建部门（需要 ADMIN）
- `GET /api/auth/departments/{id}/` - 获取部门详情
- `PUT/PATCH /api/auth/departments/{id}/` - 更新部门（需要 ADMIN）
- `DELETE /api/auth/departments/{id}/` - 删除部门（需要 ADMIN）
