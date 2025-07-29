# accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

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

    class Meta:
        verbose_name = '사용자'
        verbose_name_plural = '사용자들'
        # 테이블 명 지정
        db_table = 'auth_user'

    def __str__(self):
        return f"{self.name} ({self.email})"