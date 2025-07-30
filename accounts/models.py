# accounts/models.py

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

class CustomUserManager(UserManager):
    # 커스텀 유저 매니저 - username 없이 user 생성
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('이메일은 필수입니다.')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'trainer')  # 기본값 설정
        extra_fields.setdefault('name', 'Admin')  # 기본값 설정
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    # 커스텀 User 모델
    # Django 기본 User 모델을 확장
    # email을 로그인 필드로 사용
    # trainer/member 구분 필드 추가
    USER_TYPE_CHOICE = [
        ('trainer', 'Trainer'),
        ('member', 'Member'),
    ]

    # 기존 username 필드 제거, email을 primary로 사용
    username = None

    # 사용자 정의 필드
    email = models.EmailField(
        unique=True,
        verbose_name='이메일',
        help_text='로그인시 사용할 이메일 주소'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='이름',
        help_text='회원가입시 입력하는 실명'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='전화번호',
        help_text='회원가입시 입력하는 연락처'
    )
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICE,
        verbose_name='사용자 유형',
        help_text='trainer 또는 member'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='계정 생성 일시'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='계정 정보 수정 일시'
    )

    # 로그인 필드 : email
    USERNAME_FIELD = 'email'

    # createsuperuser 필수 입력 필드
    REQUIRED_FIELDS = ['name', 'user_type']

    # 커스텀 매니저 사용
    objects = CustomUserManager()

    class Meta:
        verbose_name = '사용자'
        verbose_name_plural = '사용자들'
        # 테이블 명 지정
        db_table = 'auth_user'

    def __str__(self):
        return f"{self.name} ({self.email})"