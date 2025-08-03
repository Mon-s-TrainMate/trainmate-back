# accounts/serializers.py

from rest_framework import serializers
from django.db import transaction
from django.contrib.auth import get_user_model, authenticate
import re

User = get_user_model()

# 회원가입 
class SignupSerializer(serializers.Serializer):
    # user_type에 따라 Trainer 또는 Member 인스턴스 직접 생성
    # Multi-table 상속
    name = serializers.CharField(max_length=100, help_text="사용자 실명")
    email = serializers.EmailField(help_text="로그인에 사용할 이메일 주소")
    password = serializers.CharField(write_only=True, help_text="10자리 이상, 영문/숫자/특수문자 포함")
    confirm_password = serializers.CharField(write_only=True, help_text="비밀번호 확인")
    user_type = serializers.ChoiceField(
        choices=[('trainer', 'Trainer'), ('member', 'Member')],
        help_text="사용자 유형 (trainer 또는 member)"
    )
    marketing_agreed = serializers.BooleanField(required=False, default=False) # 선택
    privacy_agreed = serializers.BooleanField(required=True)
    terms_agreed = serializers.BooleanField(required=True)

    def validate_email(self, value):
        # 이메일 중복 검사
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("이미 사용 중인 이메일입니다.")
        return value
    
    def validate_password(self, value):
        # 비밀번호 유효성 검사
        # 10자리 수 이상 검사
        if len(value) < 10:
            raise serializers.ValidationError("비밀번호는 10자리 이상이어야 합니다.")
        
        # 영문 포함 검사
        if not re.search(r'[a-zA-Z]', value):
            raise serializers.ValidationError("비밀번호에 영문이 한 글자 이상 포함되어야 합니다.")
        
        # 숫자 포함 검사
        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError("비밀번호에 숫자가 한 글자 이상 포함되어야 합니다.")
        
        # 특수문자 포함 검사
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', value):
            raise serializers.ValidationError("비밀번호에 특수문자가 한 글자 이상 포함되어야 합니다.")
        
        return value
    
    def validate(self, data):
        # 비밀번호 일치 검사
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("비밀번호가 일치하지 않습니다.")
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        # 사용자 생성
        from members.models import Trainer, Member
    
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user_type = validated_data.get('user_type')
        
        try:
            if user_type == 'trainer':
                # Trainer 인스턴스 직접 생성 (User 상속받음)
                user = Trainer.objects.create_user(
                    password=password,
                    **validated_data
                )
            elif user_type == 'member':
                # Member 인스턴스 직접 생성 (User 상속받음)
                user = Member.objects.create_user(
                    password=password,
                    **validated_data
                )
            else:
                user = User.objects.create_user(
                    password=password,
                    **validated_data
                )
            
            return user
            
        except Exception as e:
            print(f"오류: {e}")
            import traceback
            print(traceback.format_exc())
            raise serializers.ValidationError(f"사용자 생성 중 오류가 발생했습니다: {str(e)}")
    
# 로그인
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="가입 시 사용한 이메일 주소")
    password = serializers.CharField(write_only=True, help_text="비밀번호")

    def validate(self, data):
        # 이메일과 비밀번호로 사용자 인증
        email = data.get('email')
        password = data.get('password')

        if email and password:
            # 사용자 인증
            user = authenticate(username=email, password=password)

            if user:
                if user.is_active:
                    data['user'] = user
                    return data
                else:
                    raise serializers.ValidationError("비활성화된 계정입니다.")
            else:
                raise serializers.ValidationError("이메일 또는 비밀번호가 올바르지 않습니다.")
        else:
            raise serializers.ValidationError("이메일과 비밀번호는 모두 입력해주세요.")