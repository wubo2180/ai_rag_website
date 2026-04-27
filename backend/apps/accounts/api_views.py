from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.conf import settings
import os
import uuid

from rest_framework import generics, status, permissions
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    UserSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    DepartmentSerializer,
    UserRoleDepartmentUpdateSerializer,
    UserWithProfileSerializer,
)
from .models import UserProfile, Department
from apps.chat.models import ChatSession, ChatMessage
from apps.smart_agent.models import AgentTask, TaskStatus
from .permissions import IsAuthenticatedReadOnlyOrAdmin, IsProfileAdmin


class RegisterAPIView(APIView):
    """用户注册 API"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': '注册成功'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    """用户登录 API"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': '登录成功'
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    """用户登出 API"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': '登出成功'}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': '登出失败'}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileAPIView(generics.RetrieveUpdateAPIView):
    """用户资料 API"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class ChangePasswordAPIView(APIView):
    """修改密码 API"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': '密码修改成功'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserInfoAPIView(APIView):
    """获取当前用户信息"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_data = UserSerializer(request.user).data
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile_data = UserProfileSerializer(profile).data
        return Response({
            'user': user_data,
            'profile': profile_data
        })


class UserAvatarUploadAPIView(APIView):
    """上传用户头像"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file_obj = request.FILES.get('avatar')
        if not file_obj:
            return Response({'error': '请上传头像文件'}, status=status.HTTP_400_BAD_REQUEST)

        if not file_obj.content_type or not file_obj.content_type.startswith('image/'):
            return Response({'error': '仅支持图片文件'}, status=status.HTTP_400_BAD_REQUEST)

        max_size = 2 * 1024 * 1024
        if file_obj.size > max_size:
            return Response({'error': '头像大小不能超过2MB'}, status=status.HTTP_400_BAD_REQUEST)

        ext = os.path.splitext(file_obj.name)[1] or '.png'
        filename = f"avatars/user_{request.user.id}/{uuid.uuid4().hex}{ext}"
        saved_path = default_storage.save(filename, file_obj)

        avatar_url = request.build_absolute_uri(f"{settings.MEDIA_URL}{saved_path}")
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.avatar_url = avatar_url
        profile.save(update_fields=['avatar_url'])

        return Response({'message': '头像上传成功', 'avatar_url': avatar_url}, status=status.HTTP_200_OK)


class UserDashboardStatsAPIView(APIView):
    """用户个人中心统计（对话/智能体使用）"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        session_qs = ChatSession.objects.filter(user=user)
        message_qs = ChatMessage.objects.filter(session__user=user)
        task_qs = AgentTask.objects.filter(created_by=user)

        total_sessions = session_qs.count()
        total_messages = message_qs.count()

        total_tasks = task_qs.count()
        completed_tasks = task_qs.filter(status=TaskStatus.COMPLETED).count()
        running_tasks = task_qs.filter(status=TaskStatus.RUNNING).count()
        failed_tasks = task_qs.filter(status=TaskStatus.FAILED).count()

        success_rate = 0.0
        if total_tasks > 0:
            success_rate = round(completed_tasks / total_tasks * 100, 1)

        recent_sessions = session_qs.order_by('-updated_at')[:5]
        recent_tasks = task_qs.select_related('agent').order_by('-created_at')[:5]

        category_stats = {}
        for task in task_qs.select_related('agent'):
            category = getattr(task.agent, 'category', 'other')
            category_stats[category] = category_stats.get(category, 0) + 1

        return Response({
            'summary': {
                'total_sessions': total_sessions,
                'total_messages': total_messages,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'running_tasks': running_tasks,
                'failed_tasks': failed_tasks,
                'success_rate': success_rate,
            },
            'recent_sessions': [
                {
                    'id': s.id,
                    'title': s.title,
                    'updated_at': s.updated_at,
                }
                for s in recent_sessions
            ],
            'recent_tasks': [
                {
                    'id': str(t.id),
                    'title': t.title,
                    'status': t.status,
                    'agent_name': t.agent.display_name if t.agent else '',
                    'agent_category': t.agent.category if t.agent else '',
                    'created_at': t.created_at,
                }
                for t in recent_tasks
            ],
            'category_stats': category_stats,
        }, status=status.HTTP_200_OK)


class DepartmentListCreateAPIView(generics.ListCreateAPIView):
    """部门列表 / 创建"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticatedReadOnlyOrAdmin]


class DepartmentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """部门详情 / 更新 / 删除"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsProfileAdmin]


class UserRoleDepartmentUpdateAPIView(APIView):
    """
    管理员为用户分配角色与部门
    """
    permission_classes = [IsProfileAdmin]

    def post(self, request):
        serializer = UserRoleDepartmentUpdateSerializer(data=request.data)
        if serializer.is_valid():
            profile = serializer.update_user()
            return Response({
                'message': '用户角色/部门更新成功',
                'profile': UserProfileSerializer(profile).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListAPIView(generics.ListAPIView):
    """管理员获取所有用户及其资料"""
    queryset = User.objects.all()
    serializer_class = UserWithProfileSerializer
    permission_classes = [IsProfileAdmin]