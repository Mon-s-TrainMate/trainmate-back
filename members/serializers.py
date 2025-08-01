# members/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Trainer, Member

User = get_user_model()

class ProfileSerializer(serializers.ModelSerializer):
    # User 모델의 기본 정보
    name = serializers.CharField(source='user.name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    user_type = serializers.CharField(source='user.user_type', read_only=True)
    created_at = serializers.DateTimeField(source='user.date_joined', read_only=True)
    
    class Meta:
        model = Member  # 또는 실제 프로필 모델
        fields = [
            'name', 'email', 'user_type', 'created_at',
            'profile_image', 'age', 'height_cm', 'weight_kg', 
            'body_fat_percentage', 'muscle_mass_kg'
        ]
        extra_kwargs = {
            'profile_image': {'required': False},
            'age': {'required': False, 'help_text': '나이'},
            'height_cm': {'required': False, 'help_text': '키 (cm)'},
            'weight_kg': {'required': False, 'help_text': '몸무게 (kg)'},
            'body_fat_percentage': {'required': False, 'help_text': '체지방률 (%)'},
            'muscle_mass_kg': {'required': False, 'help_text': '골격근량 (kg)'},
        }

class ProfileUpdateSerializer(serializers.ModelSerializer):
    # 프로필 수정 serializer
    
    class Meta:
        model = Member  # 또는 실제 프로필 모델
        fields = ['age', 'height', 'weight', 'body_fat', 'muscle_mass', 'profile_image']
        extra_kwargs = {
            'age': {'required': False, 'help_text': '나이'},
            'height_cm': {'required': False, 'help_text': '키 (cm)'},
            'weight_kg': {'required': False, 'help_text': '몸무게 (kg)'},
            'body_fat_percentage': {'required': False, 'help_text': '체지방률 (%)'},
            'muscle_mass_kg': {'required': False, 'help_text': '골격근량 (kg)'},
            'profile_image': {'required': False, 'help_text': '프로필 이미지'},
        }

class UserProfileResponseSerializer(serializers.Serializer):
    # 프로필 응답용 serializer(API 문서)
    success = serializers.BooleanField()
    user = ProfileSerializer()

class ProfileUpdateResponseSerializer(serializers.Serializer):
    # 프로필 수정 응답용 serializer(API 문서)
    success = serializers.BooleanField()
    message = serializers.CharField()
    user = ProfileSerializer()


# 회원 목록 관련
class TrainerProfileSerializer(serializers.ModelSerializer):
    # 트레이너 프로필 시리얼라이저
    name = serializers.CharField(source='user.name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Trainer
        fields = ['profile_image', 'name', 'email', 'updated_at', 'is_my_profile', 'member_count']

    def get_member_count(self, obj):
        return obj.get_member_count()
    
    def get_is_my_profile(self, obj):
        return True
    
class MemberListSerializer(serializers.ModelSerializer):
    # 회원 목록용 시리얼라이저
    name = serializers.CharField(source='user.name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    is_my_profile = serializers.SerializerMethodField()

    class meta:
        model = Member
        fields = ['id', 'profile_image', 'name', 'email', 'updated_at', 'is_my_profile', 'profile_completed']

    def get_is_my_profile(self, obj):
        return False