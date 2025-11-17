from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from .models import UserProfile, Department


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ('id', 'name', 'description', 'parent', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class UserSerializer(serializers.ModelSerializer):
    """用户信息序列化器"""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'date_joined')
        read_only_fields = ('id', 'date_joined')


class UserProfileSerializer(serializers.ModelSerializer):
    """用户资料序列化器"""
    user = UserSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source='department',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = UserProfile
        fields = (
            'user',
            'nickname',
            'bio',
            'preferred_ai_model',
            'enable_deep_thinking',
            'role',
            'department',
            'department_id',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('role', 'created_at', 'updated_at')

    def update(self, instance, validated_data):
        # 普通员工不可自行修改 role，这里只允许更新其他字段
        return super().update(instance, validated_data)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
        source='department'
    )

    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'password',
            'confirm_password',
            'first_name',
            'last_name',
            'department_id'
        )

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("密码不匹配")
        return attrs

    def create(self, validated_data):
        department = validated_data.pop('department', None)
        validated_data.pop('confirm_password')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        UserProfile.objects.create(user=user, department=department)
        return user


class LoginSerializer(serializers.Serializer):
    """登录序列化器"""
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('用户名或密码错误')
            if not user.is_active:
                raise serializers.ValidationError('用户账户已被禁用')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('必须提供用户名和密码')
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """修改密码序列化器"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("新密码不匹配")
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("旧密码错误")
        return value


class UserRoleDepartmentUpdateSerializer(serializers.Serializer):
    """管理员更新用户角色与部门"""
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True)
    role = serializers.ChoiceField(choices=UserProfile.RoleChoices.choices)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )

    def update_user(self):
        user = self.validated_data['user_id']
        role = self.validated_data['role']
        department = self.validated_data.get('department_id')

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = role
        profile.department = department
        profile.save()

        # 同步 Django 后台权限
        should_be_staff = role == UserProfile.RoleChoices.ADMIN
        if user.is_staff != should_be_staff:
            user.is_staff = should_be_staff
            user.save(update_fields=['is_staff'])

        return profile


class UserWithProfileSerializer(serializers.ModelSerializer):
    """管理员查看用户及其资料"""
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'date_joined',
            'profile',
        )
        read_only_fields = fields

    def get_profile(self, obj):
        profile, _ = UserProfile.objects.get_or_create(user=obj)
        return UserProfileSerializer(profile, context=self.context).data