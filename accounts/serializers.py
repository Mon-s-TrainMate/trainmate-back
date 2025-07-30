# accounts/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ValidationError
import re

User = get_user_model()

# 회원가입 
class SignupSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    user_type = serializers.ChoiceField(choices=[('trainer', 'Trainer'), ('member', 'Member')])

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
    
    def create(self, validated_data):
        # 사용자 생성
        validated_data.pop('confirm_password')

        user = User.objects.create_user(
            # 이메일을 username으로 사용
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data['name'],
            user_type=validated_data['user_type']
        )
        
        return user
    
# 로그인
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

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