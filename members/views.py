# members/views.py

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import DatabaseError, IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from workouts.services import WorkoutRecordService
from members.models import Member, Trainer

User = get_user_model()

def get_user_profile_data(user):
    # 유저 타입에 따라 데이터 가져오기
    profile_data = {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'phone': user.phone,
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
            trainer_profile = Trainer.objects.get(user_ptr_id=user.id)
            profile_data.update({
                'profile_image': trainer_profile.profile_image.url if trainer_profile.profile_image else None,
                'age': trainer_profile.age,
                'phone': trainer_profile.phone,
                'height_cm': trainer_profile.height_cm,
                'weight_kg': trainer_profile.weight_kg,
                'body_fat_percentage': trainer_profile.body_fat_percentage,
                'muscle_mass_kg': trainer_profile.muscle_mass_kg,
            })
        elif user.user_type == 'member':
            # 로그인 유저 타입이 회원일 때
            member_profile = Member.objects.get(user_ptr_id=user.id)
            profile_data.update({
                'profile_image': member_profile.profile_image.url if member_profile.profile_image else None,
                'age': member_profile.age,
                'phone': member_profile.phone,
                'height_cm': member_profile.height_cm,
                'weight_kg': member_profile.weight_kg,
                'body_fat_percentage': member_profile.body_fat_percentage,
                'muscle_mass_kg': member_profile.muscle_mass_kg,
            })
    
    except (Trainer.DoesNotExist, Member.DoesNotExist):
        # 프로필이 아직 생성되지 않은 경우 : 기본값 유지
        pass

    return profile_data



# 내 프로필 조회/수정
@extend_schema(
    summary="내 프로필 조회/수정",
    description="GET: 내 프로필 조회, PUT/PATCH: 내 프로필 수정",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "profile_image": {"type": "string", "format": "binary", "description": "프로필 이미지"},
                "age": {"type": "integer", "description": "나이"},
                "phone": {"type": "string", "description": "전화번호"},
                "height_cm": {"type": "number", "description": "키 (cm)"},
                "weight_kg": {"type": "number", "description": "몸무게 (kg)"},
                "body_fat_percentage": {"type": "number", "description": "체지방량 (%)"},
                "muscle_mass_kg": {"type": "number", "description": "골격근량 (kg)"},
            }
        }
    },
    responses={
        200: OpenApiResponse(description="성공"),
        400: OpenApiResponse(description="유효성 검사 실패"),
        401: OpenApiResponse(description="인증 필요")
    }, tags=["프로필"]
)
@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def my_profile_view(request):
    if request.method == 'GET':
        # 프로필 조회 로직
        user = request.user
        profile_data = get_user_profile_data(user)

        return Response({
            'success': True,
            'user': profile_data
        }, status=status.HTTP_200_OK)
    
    elif request.method in ['PUT', 'PATCH']:
        # 프로필 수정 로직
        user = request.user
        updatable_fields = ['age', 'phone', 'height_cm', 'weight_kg', 'body_fat_percentage', 'muscle_mass_kg']

        try:
            if user.user_type == 'trainer':
                try:
                    trainer_profile = Trainer.objects.get(user_ptr_id=user.id)
                except Trainer.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': '트레이너 프로필을 찾을 수 없습니다.'
                    }, status=status.HTTP_404_NOT_FOUND)

                for field in updatable_fields:
                    if field in request.data:
                        setattr(trainer_profile, field, request.data[field])
                
                if 'profile_image' in request.FILES:
                    trainer_profile.profile_image = request.FILES['profile_image']
                
                trainer_profile.save()

            elif user.user_type == 'member':
                try:
                    member_profile = Member.objects.get(user_ptr_id=user.id)
                except Member.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': '회원 프로필을 찾을 수 없습니다.'
                    }, status=status.HTTP_404_NOT_FOUND)

                for field in updatable_fields:
                    if field in request.data:
                        setattr(member_profile, field, request.data[field])

                if 'profile_image' in request.FILES:
                    member_profile.profile_image = request.FILES['profile_image']
                
                member_profile.save()
            
            updated_profile = get_user_profile_data(user)

            return Response({
                'success': True,
                'message': '프로필이 수정되었습니다.',
                'user': updated_profile
            }, status=status.HTTP_200_OK)
        
        except IntegrityError:
            return Response({
                'success': False,
                'message': '데이터 무결성 제약 위반입니다. 중복된 값이 있는지 확인해주세요.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except ValidationError as e:
            return Response({
                'success': False,
                'message': '입력 데이터가 유효하지 않습니다.',
                'errors': e.message_dict if hasattr(e, 'message_dict') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except ValueError as e:
            return Response({
                'success': False,
                'message': '데이터 형식이 올바르지 않습니다.',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except DatabaseError:
            return Response({
                'success': False,
                'message': '데이터베이스 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        except (FileNotFoundError, PermissionError):
            return Response({
                'success': False,
                'message': '파일 처리 중 오류가 발생했습니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({
                'success': False,
                'message': '서버 오류가 발생했습니다. 관리자에게 문의해주세요.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



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



# 회원 목록 조회
@extend_schema(
        operation_id='list_trainer_members',
        tags=['회원관리'],
        summary='트레이너의 회원 목록 조회',
        description='트레이너의 회원 목록 조회. 회원이 로그인한 경우 빈 목록 반환',
        responses={
            200: OpenApiResponse(
            description='성공',
            examples=[
                OpenApiExample(
                    "트레이너의 회원 목록 조회 성공",
                    value={
                        "success": True,
                        "data": {
                            "trainer_profile": {
                                "profile_image": "http://example.com/profile.jpg",
                                "name": "김트레이너",
                                "email": "trainer@example.com",
                                "phone": "010-1234-5678",
                                "updated_at": "2024-01-01T00:00:00Z",
                                "is_my_profile": True,
                                "member_count": 3
                            },
                            "members": [
                                {
                                    "id": 1,
                                    "profile_image": None,
                                    "name": "김회원",
                                    "email": "member@example.com",
                                    "phone": "010-1234-5678",
                                    "updated_at": "2024-01-01T00:00:00Z",
                                    "is_my_profile": False,
                                    "profile_completed": True
                                }
                            ],
                            "total_count": 3,
                            "user_type": "trainer"
                        }
                    }
                ),
                OpenApiExample(
                    "회원이 로그인한 경우",
                    value={
                        "success": True,
                        "data": {
                            "trainer_profile": None,
                            "members": [],
                            "total_count": 0,
                            "user_type": "member",
                            "message": "회원은 트레이너 목록에 접근할 수 없습니다."
                        }
                    }
                )
            ]
        ),
        401: OpenApiResponse(description='인증 실패'),
        404: OpenApiResponse(description='트레이너 정보 없음'),
        500: OpenApiResponse(description='서버 오류')
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trainer_member_list(request):
    # 트레이너의 회원 목록 조회
    try:
        user_type = getattr(request.user, 'user_type', None)

        if user_type == 'member':
            return Response({
                'success': True,
                'data': {
                    'trainer_profile': None,
                    'members': [],
                    'total_count': 0,
                    'user_type': 'member',
                    'message': '회원은 트레이너 목록에 접근할 수 없습니다.'
                }
            }, status=status.HTTP_200_OK)
        # 로그인 유저가 트레이너인지 확인
        try:
            trainer = Trainer.objects.get(user_ptr_id=request.user.id)
        except Trainer.DoesNotExist:
            return Response({
                'error': 'TRAINER_NOT_FOUND',
                'message': '트레이너 정보를 찾을 수 없습니다.',
                'details': {
                    'user_id': request.user.id,
                    'user_type': user_type
                }
            }, status=status.HTTP_404_NOT_FOUND)

        # 회원 수 계산
        try:
            member_count = trainer.get_member_count()
        except Exception as e:
            member_count = 0

        # 트레이너 프로필 정보
        trainer_data = {
            'profile_image': trainer.profile_image.url if trainer.profile_image else None,
            'name': getattr(trainer, 'name', 'Unknown'),
            'email': getattr(trainer, 'email', 'unknown@example.com'),
            'phone': getattr(trainer, 'phone', '010-1234-5678'),
            'updated_at': trainer.updated_at.isoformat() if hasattr(trainer, 'updated_at') and trainer.updated_at else None,
            'is_my_profile': True,
            'member_count': member_count
        }

        # 담당 회원 목록 조회(활성 회원만)
        try:
            members = trainer.get_active_members()
        except Exception as e:
            members = Member.objects.none()

        # 회원 데이터 구성
        members_data = []
        for member in members:
            try:
                member_info = {
                    'id': member.id,
                    'profile_image': member.profile_image.url if member.profile_image else None,
                    'name': getattr(member, 'name', 'Unknown'),
                    'email': getattr(member, 'email', 'unknown@example.com'),
                    'phone': getattr(trainer, 'phone', '010-1234-5678'),
                    'updated_at': member.updated_at.isoformat() if hasattr(member, 'updated_at') and member.updated_at else None,
                    'is_my_profile': False,
                    'profile_completed': getattr(member, 'profile_completed', False)
                }
                members_data.append(member_info)
            except Exception as e:
                continue
        
        # 트레이너에게 소속된 회원이 없을 경우 메시지 추가
        response_data = {
            'trainer_profile': trainer_data,
            'members': members_data,
            'total_count': len(members_data),
            'user_type': 'trainer'
        }

        # 소속 회원이 없는 경우 안내 메시지 추가
        if len(members_data) == 0:
            response_data['message'] = '현재 담당 회원이 없습니다. 새로운 회원을 등록해보세요.'

        return Response({
            'success': True,
            'data': response_data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'error': 'INTERNAL_SERVER_ERROR',
            'message': '서버 오류가 발생했습니다.'
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
        trainer = get_object_or_404(Trainer, user_ptr_id=request.user.id)

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
            member = Member.objects.get(user_ptr_id=target_user.id)
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
                    'current_trainer': member.assigned_trainer.name
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
                    'name': target_user.name,
                    'email': target_user.email,
                    'trainer_name': trainer.name,
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
        trainer = get_object_or_404(Trainer, user_ptr_id=request.user.id)

        query = request.GET.get('query', '').strip()
        if not query:
            return Response({
                'error': 'MISSING_QUERY',
                'message': '검색어를 입력해주세요.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 트레이너가 미배정된 회원들만 검색
        unassigned_member_user_ids = Member.objects.filter(
            assigned_trainer=None # 트레이너가 배정되지 않은 회원들
        ).values_list('user_ptr_id', flat=True)

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
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        return Response({
            'error': 'INTERNAL_SERVER_ERROR',
            'message': '서버 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@extend_schema(
    operation_id='get_trainer_detail',
    tags=['프로필'],
    summary='트레이너 상세 정보 조회',
    description='특정 트레이너의 상세 정보를 조회합니다.',
    parameters=[
        OpenApiParameter(
            name='trainer_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='조회할 트레이너의 ID',
            required=True
        )
    ],
    responses={
        200: OpenApiResponse(description='트레이너 정보 조회 성공'),
        401: OpenApiResponse(description='인증 필요'),
        404: OpenApiResponse(description='트레이너를 찾을 수 없음'),
        500: OpenApiResponse(description='서버 오류')
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trainer_detail(request, trainer_id):
    # 트레이너 상세 조회
    try:
        # 트레이너 정보 가져오기
        try:
            trainer = Trainer.objects.get(id=trainer_id)
        except Trainer.DoesNotExist:
            return Response({
                'error': 'TRAINER_NOT_FOUND',
                'message': '트레이너를 찾을 수 없습니다.'
            }, status=status.HTTP_404_NOT_FOUND)

        # 트레이너 상세 정보 구성
        trainer_data = {
            'id': trainer.id,
            'profile_image': trainer.profile_image.url if trainer.profile_image else None,
            'name': getattr(trainer, 'name', 'Unknown'),
            'email': getattr(trainer, 'email', 'unknown@example.com'),
            'phone': getattr(trainer, 'phone', '010-1234-5678'),
            'age': getattr(trainer, 'age', None),
            'height_cm': float(trainer.height_cm) if trainer.height_cm else None,
            'weight_kg': float(trainer.weight_kg) if trainer.weight_kg else None,
            'body_fat_percentage': float(trainer.body_fat_percentage) if trainer.body_fat_percentage else None,
            'muscle_mass_kg': float(trainer.muscle_mass_kg) if trainer.muscle_mass_kg else None,
            'profile_completed': getattr(trainer, 'profile_completed', False),
            'is_active': getattr(trainer, 'is_active', True),
            'created_at': trainer.date_joined.isoformat() if hasattr(trainer, 'date_joined') else None,
            'updated_at': trainer.updated_at.isoformat() if hasattr(trainer, 'updated_at') and trainer.updated_at else None,
            'is_my_profile': request.user.id == trainer.user_ptr_id,
            'member_count': trainer.get_member_count() if hasattr(trainer, 'get_member_count') else 0
        }

        return Response({
            'success': True,
            'data': {
                'trainer': trainer_data
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': 'INTERNAL_SERVER_ERROR',
            'message': '서버 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@extend_schema(
    operation_id='get_member_detail',
    tags=['프로필'],
    summary='회원 상세 정보 조회',
    description='특정 회원의 상세 정보를 조회합니다.',
    parameters=[
        OpenApiParameter(
            name='member_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='조회할 회원의 ID',
            required=True
        )
    ],
    responses={
        200: OpenApiResponse(description='회원 정보 조회 성공'),
        401: OpenApiResponse(description='인증 실패'),
        403: OpenApiResponse(description='권한 없음'),
        404: OpenApiResponse(description='회원을 찾을 수 없음'),
        500: OpenApiResponse(description='서버 오류')
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def member_detail(request, member_id):
    # 회원 상세 정보 조회
    try:
        user_data = None
        user_type = None
        # 조회하려는 회원 정보 가져오기
        try:
            member = Member.objects.get(id=member_id)
            user_type = "member"
        
        # 회원 상세 정보 구성
            user_data = {
                'id': member.id,
                'profile_image': member.profile_image.url if member.profile_image else None,
                'name': getattr(member, 'name', 'Unknown'),
                'email': getattr(member, 'email', 'unknown@example.com'),
                'phone': getattr(member, 'phone', '010-1234-5678'),
                'age': getattr(member, 'age', None),
                'height_cm': float(member.height_cm) if member.height_cm else None,
                'weight_kg': float(member.weight_kg) if member.weight_kg else None,
                'body_fat_percentage': float(member.body_fat_percentage) if member.body_fat_percentage else None,
                'muscle_mass_kg': float(member.muscle_mass_kg) if member.muscle_mass_kg else None,
                'profile_completed': getattr(member, 'profile_completed', False),
                'is_active': getattr(member, 'is_active', True),
                'created_at': member.date_joined.isoformat() if hasattr(member, 'date_joined') else None,
                'updated_at': member.updated_at.isoformat() if hasattr(member, 'updated_at') and member.updated_at else None,
                'is_my_profile': request.user.id == member.user_ptr_id,
            }

            # 트레이너 정보 추가
            if member.assigned_trainer:
                user_data['trainer_info'] = {
                    'id': member.assigned_trainer.id,
                    'name': getattr(member.assigned_trainer, 'name', 'Unknown'),
                    'email': getattr(member.assigned_trainer, 'email', 'unknown@example.com'),
                    'phone': getattr(member.assigned_trainer, 'phone', '010-1234-5678'),
                    'profile_image': member.assigned_trainer.profile_image.url if member.assigned_trainer.profile_image else None
                }
            else:
                user_data['trainer_info'] = None

        except Member.DoesNotExist:
            try:
                trainer = Trainer.objects.get(id=member_id)
                user_type = "trainer"
                
                user_data = {
                    'id': trainer.id,
                    'user_type': 'trainer',
                    'profile_image': trainer.profile_image.url if trainer.profile_image else None,
                    'name': getattr(trainer, 'name', 'Unknown'),
                    'email': getattr(trainer, 'email', 'unknown@example.com'),
                    'phone': getattr(trainer, 'phone', '010-1234-5678'),
                    'age': getattr(trainer, 'age', None),
                    'height_cm': float(trainer.height_cm) if trainer.height_cm else None,
                    'weight_kg': float(trainer.weight_kg) if trainer.weight_kg else None,
                    'body_fat_percentage': float(trainer.body_fat_percentage) if trainer.body_fat_percentage else None,
                    'muscle_mass_kg': float(trainer.muscle_mass_kg) if trainer.muscle_mass_kg else None,
                    'profile_completed': getattr(trainer, 'profile_completed', False),
                    'is_active': getattr(trainer, 'is_active', True),
                    'created_at': trainer.date_joined.isoformat() if hasattr(trainer, 'date_joined') else None,
                    'updated_at': trainer.updated_at.isoformat() if hasattr(trainer, 'updated_at') and trainer.updated_at else None,
                    'is_my_profile': request.user.id == trainer.user_ptr_id,
                    'member_count': trainer.get_member_count() if hasattr(trainer, 'get_member_count') else 0
                }
                
                user_data['trainer_info'] = None  # 트레이너는 담당 트레이너 없음
                
            except Trainer.DoesNotExist:
                # 3. 둘 다 없으면 404 반환
                return Response({
                    'detail': 'User not found',
                    'code': 'user_not_found'
                }, status=status.HTTP_404_NOT_FOUND)

        # 운동 기록 조회(workouts에서 처리)
        try:
            if user_type == "member":
                # 회원의 운동 기록 조회
                workout_data = WorkoutRecordService.get_member_workout_records(member_id)
            else:
                # 트레이너의 경우: 일단 빈 배열 (나중에 트레이너가 진행한 운동들 조회 로직 추가 가능)
                workout_data = {
                    'workout_records': [],
                    'total_workouts': 0,
                    'has_records': False
                }


        except Exception as e:
            workout_data = {
                'workout_records': [],
                'total_workouts': 0,
                'has_records': False
            }

        return Response({
            'success': True,
            'data': {
                'member': user_data,  # 프론트엔드 호환성을 위해 'member' 키 유지
                **workout_data
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'error': 'INTERNAL_SERVER_ERROR',
            'message': '서버 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)