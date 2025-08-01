# members/views.py

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from .serializers import TrainerProfileSerializer, MemberListSerializer

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



# 내 프로필 조회
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



# 다른 사용자 프로필 조회
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



# 프로필 수정
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



# 회원 목록 조회
@extend_schema(
        operation_id='get_trainer_members',
        tags=['회원관리'],
        summary='트레이너의 회원 목록 조회',
        description='트레이너의 회원 목록 조회',
        responses={
            200: OpenApiResponse(description='성공'),
            401: OpenApiResponse(description='인증 실패'),
            403: OpenApiResponse(description='트레이너 권한 필요'),
            404: OpenApiResponse(description='트레이너 정보 없음'),
            500: OpenApiResponse(description='서버 오류')
        }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trainer_member_list(request):
    # 트레이너의 회원 목록 조회
    try:
        # 현재 로그인한 사용자가 트레이너인지 확인
        print(request.user.id)
        # trainer = get_object_or_404(Trainer, user_id=request.user.id)
        trainer = Trainer.objects.get(user_id=request.user.id)
        print(trainer)

        # 내 프로필 정보
        trainer_data = {
            'profile_image': trainer.profile_image.url if trainer.profile_image else None,
            'name': trainer.user.name,
            'email': trainer.user.email,
            'updated_at': trainer.updated_at,
            'is_my_profile': True, # 내 프로필 구분용
            'member_count': trainer.get_member_count()
        }

        # 담당 회원 목록(활성 회원만)
        members = trainer.get_active_members().select_related('user').order_by('-updated_at')

        members_data = []
        for member in members:
            members_data.append({
                'id': member.id,
                'profile_image': member.profile_image.url if member.profile_image else None,
                'email': member.user.email,
                'name': member.user.name,
                'updated_at': member.updated_at,
                'is_my_profile': False,
                'profile_completed': member.profile_completed
            })
        return Response({
            'success': True,
            'data': {
                'trainer_profile': trainer_data,
                'members': members_data,
                'total_count': len(members_data)
            }
        }, status=status.HTTP_200_OK)
    
    except Trainer.DoesNotExist:
        return Response({
            'error': 'TRAINER_NOT_FOUND',
            'message': '트레이너 정보를 찾을 수 없습니다.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({
            'error': 'INTERNAL_SERVER_ERROR',
            'message': '서버 오류가 발생했습니다'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# 회원 등록
@extend_schema(
    operation_id='register_member_to_trainer',
    tags=['회원관리'],
    summary='트레이너의 회원 등록',
    description='검색된 회원을 현재 로그인한 트레이너의 담당 회원으로 등록합니다.',
    request={
        'application/json': {
        'type': 'object',
        'properties': {
            'user_id': {
                'type': 'integer',
                'description': '등록할 회원의 User ID'
            }
        },'required': ['user_id']}
    },
    responses={
        201: OpenApiResponse(description='등록 성공'),
        400: OpenApiResponse(description='잘못된 요청'),
        401: OpenApiResponse(description='인증 실패'),
        404: OpenApiResponse(description='회원을 찾을 수 없음'),
        409: OpenApiResponse(description='이미 등록된 회원')
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_member_to_trainer(request):
    # 트레이너의 회원 등록 - 기존 Member에 trainer_id 업데이트
    try:
        # 현재 사용자가 트레이너인지 확인
        trainer = get_object_or_404(Trainer, user=request.user)

        user_id = request.data.get('user_id')
        if not user_id:
            return Response({
                'error': 'MISSING_USER_ID',
                'message': '등록할 회원의 아이디가 필요합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 등록할 사용자 확인
            target_user = User.objects.get(id=user_id, user_type='member')
        except User.DoesNotExist:
            return Response({
                'error': 'USER_NOT_FOUND',
                'message': '해당 회원을 찾을 수 없습니다.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Member 프로필 확인
        try:
            member = Member.objects.get(user=target_user)
        except Member.DoesNotExist:
            return Response({
                'error': 'MEMBER_PROFILE_NOT_FOUND',
                'message': '회원 프로필을 찾을 수 없습니다.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 이미 다른 트레이너에게 등록된 회원인지 확인
        if member.trainer is not None:
            return Response({
                'error': 'MEMBER_ALREADY_ASSIGNED',
                'message': '이미 다른 트레이너의 회원입니다.',
                'details': {
                    'member_name': target_user.name,
                    'current_trainer': member.trainer.user.name
                }
            }, status=status.HTTP_409_CONFLICT)
        
        # 트레이너의 회원 등록(기존 Member 레코드 업데이트)
        member.trainer = trainer
        member.save()

        return Response({
            'success': True,
            'message': '회원이 성공적으로 등록되었습니다.',
            'data': {
                'member': {
                    'id': member.id,
                    'name': member.user.name,
                    'email': member.user.email,
                    'trainer_name': trainer.user.name,
                    'assigned_at': member.updated_at
                }
            }
        }, status=status.HTTP_200_OK) # 201(생성완료) -> 생성이 아닌 업데이트
    
    except Exception as e:
        return Response({
            'error': 'INTERNAL_SERVER_ERROR',
            'message': '서버 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# 회원 검색
@extend_schema(
    operation_id='search_users_for_trainer',
    tags=['회원관리'],
    summary='회원 검색',
    description='트레이너가 등록할 회원을 이름 또는 이메일로 검색합니다.',
    parameters=[
        OpenApiParameter(
            name='query',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='검색할 회원의 이름 또는 이메일',
            required=True
        )
    ],
    responses={
        200: OpenApiResponse(description='검색 성공'),
        400: OpenApiResponse(description='잘못된 요청'),
        401: OpenApiResponse(description='인증 실패'),
        404: OpenApiResponse(description='검색 결과 없음')
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_users_for_registration(request):
    # 트레이너가 등록할 회원 검색
    try:
        # 현재 사용자가 트레이너인지 확인
        trainer = get_object_or_404(Trainer, user=request.user)

        query = request.GET.get('query', '').strip()
        if not query:
            return Response({
                'error': 'MISSING_QUERY',
                'message': '검색어를 입력해주세요.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 트레이너가 미배정된 회원들만 검색
        unassigned_member_user_ids = Member.objects.filter(
            trainer=None # 트레이너가 배정되지 않은 회원들
        ).values_list('user_id', flat=True)

        # 검색 실행
        users = User.objects.filter(
            Q(name__icontains=query) | Q(email__icontains=query), # 이름 또는 이메일로 검색
            user_type='member',
            id__in=unassigned_member_user_ids # 미배정 회원만
        ).exclude(
            id=request.user.id # 본인 제외
        )[:10]

        if not users.exists():
            return Response({
                'error': 'NO_SEARCH_RESULTS',
                'message': '검색 조건에 맞는 회원이 없습니다.',
                'details': {
                    'query': query,
                    'suggestion': '이름 또는 이메일을 정확히 입력해주세요.'
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 검색 결과 반환
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'user_type': user.user_type,
                'date_joined': user.date_joined
            })

        return Response({
            'success': True,
            'data': {
                'users': users_data,
                'total_count': len(users_data),
                'query': query
            }
        }, status=status.HTTP_200_OK)
    
    except Trainer.DoesNotExist:
        return Response({
            'error': 'TRAINER_NOT_FOUND',
            'message': '트레이너 정보를 찾을 수 없습니다.'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'error': 'INTERNAL_SERVER_ERROR',
            'message': '서버 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)