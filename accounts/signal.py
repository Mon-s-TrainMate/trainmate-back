from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    # User 생성 후 자동으로 해당 프로필 생성
    # Trainer -> user_id 외래키, Trainer 테이블에 레코드 생성
    # Member -> user_id 외래키, Member 테이블에 레코드 생성(trainer_id는 null, 추후 수정 가능)
    if created:
        # 회원을 새로 생성한 경우
        if instance.user_type == 'TRAINER':
            from members.models import Trainer
            trainer_profile = Trainer.objects.create(user=instance)
            print(f"트레이너 프로필 생성 완료 : {instance.email} -> Trainer ID: {trainer_profile.id}")

        elif instance.user_type == 'member':
            from members.models import Member
            member_profile = Member.objects.create(
                user=instance,
                trainer=None
            )
            print(f"회원 프로필 생성 완료: {instance.email} -> Member ID: {member_profile.id} (소속 트레이너가 없습니다.)")

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # User 정보 수정 시 프로필도 함께 업데이트
    if instance.user_type == 'TRAINER':
        from members.models import Trainer
        if hasattr(instance, 'trainer_profile'):
            instance.trainer_profile.save()
    elif instance.user_type == 'member':
        from members.models import Member
        if hasattr(instance, 'member_profile'):
            instance.member_profile.save()