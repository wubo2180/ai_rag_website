from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile

# REST Framework imports
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    UserSerializer, 
    UserProfileSerializer, 
    UserRegistrationSerializer, 
    LoginSerializer,
    ChangePasswordSerializer
)

def home(request):
    """首页重定向到聊天页面"""
    return redirect('chat_index')

def login_page(request):
    """登录页面视图"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'欢迎回来，{username}！')
                return redirect('profile')
            else:
                messages.error(request, '用户名或密码错误')
        else:
            messages.error(request, '用户名或密码错误')
    else:
        form = AuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def register_page(request):
    """注册页面视图"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if password1 != password2:
            messages.error(request, '两次输入的密码不一致')
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, '用户名已存在')
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, '邮箱已被注册')
            return render(request, 'accounts/register.html')
        
        try:
            user = User.objects.create_user(username=username, email=email, password=password1)
            UserProfile.objects.create(user=user)
            messages.success(request, '注册成功！请登录')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'注册失败：{str(e)}')
    
    return render(request, 'accounts/register.html')

def profile_view(request):
    """个人资料页面视图（用于传统URL）"""
    return profile(request)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """用户登录API"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({
            'success': False,
            'message': '请提供用户名和密码'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(username=username, password=password)
    
    if user is not None:
        login(request, user)
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'success': True,
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            },
            'message': '登录成功'
        })
    else:
        return Response({
            'success': False,
            'message': '用户名或密码错误'
        }, status=status.HTTP_401_UNAUTHORIZED)

def logout_page(request):
    """登出页面视图（支持GET请求）"""
    logout(request)
    messages.success(request, '您已成功退出登录')
    return redirect('login')

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """用户登出API"""
    try:
        # 删除用户的token
        request.user.auth_token.delete()
    except:
        pass
    
    logout(request)
    
    return Response({
        'success': True,
        'message': '退出登录成功'
    })

@login_required
def profile(request):
    # 确保用户有profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # 获取用户统计数据
    try:
        from apps.chat.models import ChatSession
        from apps.knowledge.models import Knowledge, Document
        
        chat_sessions_count = ChatSession.objects.filter(user=request.user).count()
        try:
            knowledge_count = Knowledge.objects.filter(created_by=request.user).count()
            documents_count = Document.objects.filter(uploaded_by=request.user).count()
        except:
            knowledge_count = 0
            documents_count = 0
        
        recent_sessions = ChatSession.objects.filter(user=request.user).order_by('-updated_at')[:5]
    except:
        chat_sessions_count = 0
        knowledge_count = 0
        documents_count = 0
        recent_sessions = []
    
    context = {
        'chat_sessions_count': chat_sessions_count,
        'knowledge_count': knowledge_count,
        'documents_count': documents_count,
        'recent_sessions': recent_sessions,
    }
    
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # 更新用户基本信息
        request.user.username = request.POST.get('username', request.user.username)
        request.user.email = request.POST.get('email', request.user.email)
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name = request.POST.get('last_name', request.user.last_name)
        request.user.save()
        
        # 更新用户资料
        profile.bio = request.POST.get('bio', profile.bio)
        # TODO: 头像功能暂时禁用，需要在模型中添加 avatar 字段
        # if 'avatar' in request.FILES:
        #     profile.avatar = request.FILES['avatar']
        profile.save()
        
        messages.success(request, '个人资料更新成功！')
        return redirect('profile')
    
    return render(request, 'accounts/edit_profile.html')

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, '密码修改成功！')
            return redirect('profile')
        else:
            messages.error(request, '密码修改失败，请检查输入的信息。')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'accounts/change_password.html', {'form': form})

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """更新用户个人资料"""
    try:
        user = request.user
        profile = user.profile
        
        # 更新用户基本信息
        user.email = request.data.get('email', user.email)
        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.save()
        
        # 更新用户资料
        profile.bio = request.data.get('bio', profile.bio)
        profile.save()
        
        return Response({
            'success': True,
            'message': '个人资料更新成功'
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_api(request):
    """修改密码"""
    from django.contrib.auth import authenticate
    
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    
    if not current_password or not new_password:
        return Response({
            'success': False,
            'message': '请提供当前密码和新密码'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # 验证当前密码
    user = authenticate(username=request.user.username, password=current_password)
    if not user:
        return Response({
            'success': False,
            'message': '当前密码错误'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # 设置新密码
    try:
        request.user.set_password(new_password)
        request.user.save()
        
        return Response({
            'success': True,
            'message': '密码修改成功'
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': '密码修改失败'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_avatar(request):
    """上传头像"""
    if 'file' not in request.FILES:
        return Response({
            'success': False,
            'message': '请选择要上传的文件'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    file = request.FILES['file']
    
    # 验证文件类型
    if not file.content_type.startswith('image/'):
        return Response({
            'success': False,
            'message': '只能上传图片文件'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # 验证文件大小（2MB）
    if file.size > 2 * 1024 * 1024:
        return Response({
            'success': False,
            'message': '文件大小不能超过2MB'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # TODO: 头像功能暂时禁用，需要在模型中添加 avatar 字段
        # profile = request.user.profile
        # profile.avatar = file
        # profile.save()
        
        return Response({
            'success': False,
            'message': '头像功能暂时不可用'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)
    except Exception as e:
        return Response({
            'success': False,
            'message': '头像上传失败'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ======================== REST API 视图类 ========================

class RegisterAPIView(generics.CreateAPIView):
    """用户注册 API"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
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
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
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
        try:
            profile = request.user.profile
            profile_data = UserProfileSerializer(profile).data
            return Response({
                'user': user_data,
                'profile': profile_data
            })
        except UserProfile.DoesNotExist:
            # 如果用户没有profile，则创建一个
            profile = UserProfile.objects.create(user=request.user)
            profile_data = UserProfileSerializer(profile).data
            return Response({
                'user': user_data,
                'profile': None
            })