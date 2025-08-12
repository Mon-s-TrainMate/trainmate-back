# members/models.py

from django.db import models
from accounts.models import User

class Trainer(User):
    # 트레이너 프로필 모델
    # User 상속
    # 프로필 정보 및 신체 정보 관리
    # 회원관리
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
    profile_completed = models.BooleanField(
        default=False,
        verbose_name='프로필 완성 여부',
        help_text='프로필 정보가 모두 입력되었는지 확인'
    )

    class Meta:
        verbose_name = '트레이너'
        verbose_name_plural = '트레이너들'
        db_table = 'trainer'

    def __str__(self):
        return f"트레이너 : {self.name}"
    
    def get_member_count(self):
        # 담당 회원 수
        try:
            # related_name='members'를 통한 역참조 사용
            return self.members.filter(is_active=True).count()
        except Exception as e:
            return 0
        
    def get_active_members(self):
        try:
            return self.members.filter(is_active=True)
        except Exception as e:
            return Member.objects.none()


class Member(User):
    # 회원 프로필 모델
    # User 상속
    # Trainer와 다대일 관계(한 트레이너가 여러 회원 담당)
    assigned_trainer = models.ForeignKey(
        Trainer,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name='담당 트레이너',
        help_text='소속 트레이너',
        null=True,
        blank=True,
        db_column='trainer_id'
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
    
    class Meta:
        verbose_name = '회원'
        verbose_name_plural = '회원들'
        db_table = 'member'
    
    def __str__(self):
        trainer_name = self.assigned_trainer.name if self.assigned_trainer else "미배정"
        if hasattr(self, 'name') and self.name:
            return f"회원: {self.name} (담당: {trainer_name})"
        else:
            # User 모델의 기본 필드들 사용
            return f"회원: {self.username} (담당: {trainer_name})"
    
    @property
    def trainer(self):
        return self.assigned_trainer