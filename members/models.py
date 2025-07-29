# members/models.py

from django.db import models
from accounts.models import User

class Trainer(models.Model):
    # 트레이너 프로필 모델
    # User 모델과 1:1 관계
    # 프로필 정보 및 신체 정보 관리
    # 회원관리

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='trainer_profile',
        verbose_name='사용자',
        help_text='연결된 사용자 계정'
    )
    profile_image = models.ImageField(
        upload_to='trainer_profile/',
        blank=True,
        null=True,
        verbose_name='프로필 이미지',
        help_text='프로필 수정에서 업로드'
    )
    age = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='나이',
        help_text='프로필 수정에서 입력'
    )
    height_cm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='키(cm)',
        help_text='프로필 수정에서 입력'
    )
    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='몸무게(kg)',
        help_text='프로필 수정에서 입력'
    )
    body_fat_percentage = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='체지방률(%)',
        help_text='키/몸무게 기반 자동 계산'
    )
    muscle_mass_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='골격근량(kg)',
        help_text='키/몸무게 기반 자동 계산'
    )
    profile_complated = models.BooleanField(
        default=False,
        verbose_name='프로필 완성 여부',
        help_text='프로필 정보가 모두 입력되었는지 확인'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='수정 일시'
    )

    class Meta:
        verbose_name = '트레이너'
        verbose_name_plural = '트레이너들'
        db_table = 'trainer'

    def __str__(self):
        return f"트레이너 : {self.user.name}"
    
    def get_member_count(self):
        # 담당 회원 수
        return self.members.count()
    
    def get_active_members(self):
        # 활성 회원 목록 반환
        # is_active : django에서 제공하는 기본 사용자 관리 시스템
        # False : 로그인 불가능, 정지, 탈퇴 등. 데이터는 유지 되지만 서비스 이용 불가 상태
        return self.members.filter(user__is_active=True)
    


class Member(models.Model):
    # 회원 프로필 모델
    # User 모델과 1:1 관계
    # Trainer와 다대일 관계(한 트레이너가 여러 회원 담당)

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='member_profile',
        verbose_name='사용자',
        help_text='연결된 사용자 계정'
    )
    trainer = models.ForeignKey(
        Trainer,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name='담당 트레이너',
        help_text='소속 트레이너'
    )
    profile_image = models.ImageField(
        upload_to='member_profile/',
        blank=True,
        null=True,
        verbose_name='프로필 이미지',
        help_text='프로필 수정에서 업로드'
    )
    age = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='나이',
        help_text='프로필 수정에서 입력'
    )
    height_cm = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='키(cm)',
        help_text='프로필 수정에서 입력'
    )
    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='몸무게(kg)',
        help_text='프로필 수정에서 입력'
    )
    body_fat_percentage = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='체지방률(%)',
        help_text='키/몸무게 기반 자동 계산'
    )
    muscle_mass_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='골격근량(kg)',
        help_text='키/몸무게 기반 자동 계산'
    )
    profile_completed = models.BooleanField(
        default=False,
        verbose_name='프로필 완성 여부',
        help_text='프로필 정보가 모두 입력되었는지 확인'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='수정일시'
    )
    
    class Meta:
        verbose_name = '회원'
        verbose_name_plural = '회원들'
        db_table = 'member'
    
    def __str__(self):
        return f"회원: {self.user.name} (담당: {self.trainer.user.name})"