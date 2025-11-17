from django.contrib.auth.models import User

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