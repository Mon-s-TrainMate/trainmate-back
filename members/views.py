# members/views.py

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from members.models import Member, Trainer

User = get_user_model()

def get_user_profile_data(user):
    # 유저 타입에 따라 데이터 가져오기
    profile_data = {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'user_type': user.user_type,
        'created_at': user.date_joined,
        # 기본값
        'profile_image': None,
        'age': None,
        'height_cm': None,
        'weight_kg': None,
        'body_fat_percentage': None,
        'muscle_mass_kg': None,
    }

    try:
        if user.user_type == 'trainer':
            # 로그인 유저 타입이 트레이너일 때
            trainer_profile = Trainer.objects.get(user=user)
            profile_data.update({
                'profile_image': trainer_profile.profile_image.url if trainer_profile.profile_image else None,
                'age': trainer_profile.age,
                'height_cm': trainer_profile.height_cm,
                'weight_kg': trainer_profile.weight_kg,
                'body_fat_percentage': trainer_profile.body_fat_percentage,
                'muscle_mass_kg': trainer_profile.muscle_mass_kg,
            })
        elif user.user_type == 'member':
            # 로그인 유저 타입이 회원일 때
            member_profile = Member.objects.get(user=user)
            profile_data.update({
                'profile_image': member_profile.profile_image.url if member_profile.profile_image else None,
                'age': member_profile.age,
                'height_cm': member_profile.height_cm,
                'weight_kg': member_profile.weight_kg,
                'body_fat_percentage': member_profile.body_fat_percentage,
                'muscle_mass_kg': member_profile.muscle_mass_kg,
            })
    
    except (Trainer.DoesNotExist, Member.DoesNotExist):
        # 프로필이 아직 생성되지 않은 경우 : 기본값 유지
        pass

    return profile_data



@extend_schema(
    summary="내 프로필 조회",
    description="현재 로그인한 사용자의 프로필 정보를 조회합니다.",
    responses={
        200: OpenApiResponse(
            response=dict,
            description="프로필 조회 성공",
            examples=[
                OpenApiExample(
                    "프로필 조회 성공",
                    value={
                        "success": True,
                        "user": {
                            "id": 1,
                            "name": "홍길동",
                            "email": "hong@example.com",
                            "user_type": "trainer",
                            "profile_image": "http://example.com/profile.jpg",
                            "age": 20,
                            "height_cm": 175,
                            "weight_kg": 70,
                            "body_fat_percentage": 15.5,
                            "muscle_mass_kg": 35.2,
                            "created_at": "2024-01-01T00:00:00Z"
                        }
                    }
                )
            ]
        ), 401: OpenApiResponse(description="인증 필요")
    }, tags=["프로필"]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_profile(request):
    # 내 프로필 조회
    user = request.user
    profile_data = get_user_profile_data(user)

    return Response({
        'success': True,
        'user': profile_data
    }, status=status.HTTP_200_OK)



@extend_schema(
    summary="다른 사용자 프로필 조회",
    description="특정 사용자의 공개 프로필 정보를 조회합니다.",
    responses={
        200: OpenApiResponse(description="프로필 조회 성공"),
        404: OpenApiResponse(description="사용자를 찾을 수 없음"),
        401: OpenApiResponse(description="인증 필요")
    }, tags = ["프로필"]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request, user_id):
    # 다른 사용자 프로필 조회
    target_user = get_object_or_404(User, id=user_id)
    profile_data = get_user_profile_data(target_user)

    return Response({
        'success': True,
        'user': profile_data
    }, status=status.HTTP_200_OK)



@extend_schema(
    summary="프로필 수정",
    description="현재 로그인한 사용자의 프로필 정보를 수정합니다.",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "profile_image": {"type": "string", "format": "binary", "description": "프로필 이미지"},
                "age": {"type": "integer", "description": "나이"},
                "height_cm": {"type": "number", "description": "키 (cm)"},
                "weight_kg": {"type": "number", "description": "몸무게 (kg)"},
                "body_fat_percentage": {"type": "number", "description": "체지방량 (%)"},
                "muscle_mass_kg": {"type": "number", "description": "골격근량 (kg)"},
            }
        }
    }, responses={
        200: OpenApiResponse(description="프로필 수정 성공"),
        400: OpenApiResponse(description="유효성 검사 실패"),
        401: OpenApiResponse(description="인증 필요")
    }, tags=["프로필"]
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_my_profile(request):
    # 프로필 수정
    user = request.user

    # 수정 가능 필드
    updatable_fields = ['age', 'height_cm', 'weight_kg', 'body_fat_percentage', 'muscle_mass_kg']

    try:
        if user.user_type == 'trainer':
            trainer_profile, created = Trainer.objects.get_or_create(user=user)

            for field in updatable_fields:
                if field in request.data:
                    setattr(trainer_profile, field, request.data[field])
            
            # 프로필 이미지
            if 'profile_image' in request.FILES:
                trainer_profile.profile_image = request.FILES['profile_image']
            
            trainer_profile.save()

        elif user.user_type == 'member':
            member_profile, created = Member.objects.get_or_create(user=user)

            for field in updatable_fields:
                if field in request.data:
                    setattr(member_profile, field, request.data[field])

            # 프로필 이미지
            if 'profile_image' in request.FILES:
                member_profile.profile_image = request.FILES['profile_image']
            
            member_profile.save()
        
        updated_profile = get_user_profile_data(user)

        return Response({
            'success': True,
            'message': '프로필이 수정되었습니다.',
            'user': updated_profile
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'success': False,
            'message': '프로필 수정에 실패했습니다.',
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)