# accounts/views.py

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, DatabaseError
from drf_spectacular.utils import extend_schema_view,extend_schema, OpenApiResponse, OpenApiExample
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken, TokenBackendError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from .serializers import SignupSerializer, LoginSerializer

User = get_user_model()

# 사용자 JWT 토큰 생성
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    # 커스텀 claim 추가
    refresh['user_type'] = user.user_type

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }



# refresh token을 받아 새로운 access token 발급
@extend_schema_view(
    post=extend_schema(
        operation_id='token_refresh',
        summary="토큰 갱신",
        description="Refresh token을 사용하여 새로운 access token을 발급받습니다.",
        request=TokenRefreshSerializer,
        responses={
            200: OpenApiResponse(
                response=dict,
                description="토큰 갱신 성공",
                examples=[
                    OpenApiExample(
                        "토큰 갱신 성공",
                        value={
                            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjk5..."
                        }
                    )
                ]
            ),
            401: OpenApiResponse(
                response=dict,
                description="유효하지 않은 refresh token",
                examples=[
                    OpenApiExample(
                        "토큰 갱신 실패",
                        value={
                            "detail": "Token is invalid or expired",
                            "code": "token_not_valid"
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="잘못된 요청")
        },
        tags=["인증"]
    )
)
class CustomTokenRefreshView(TokenRefreshView):
    pass



@extend_schema(
    operation_id='user_signup',
    summary="회원가입",
    description="새로운 사용자를 등록합니다. trainer 또는 member로 구분하여 가입할 수 있습니다.",
    request=SignupSerializer,
    responses={
        201: OpenApiResponse(
            response=dict,
            description="회원가입 성공",
            examples=[
                OpenApiExample(
                    "회원가입 성공",
                    value={
                        "success": True,
                        "message": "회원가입이 완료되었습니다.",
                        "user": {
                            "id": 1,
                            "name": "홍길동",
                            "email": "hong@example.com",
                            "user_type": "trainer",
                            "terms_agreed": "True",
                            "privacy_agreed": "True",
                            "marketing_agreed": "True"
                        }
                    }
                )
            ]
        ),
        400: OpenApiResponse(description="유효성 검사 실패")
    },
    tags=["인증"]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    # 회원가입 api
    try:
        serializer = SignupSerializer(data=request.data)

        if serializer.is_valid():
            try:
                user = serializer.save()

                return Response({
                    'success': True,
                    'message': '회원가입이 완료되었습니다.',
                    'user': {
                        'id': user.id,
                        'name': user.name,
                        'email': user.email,
                        'user_type': user.user_type
                    }
                }, status=status.HTTP_201_CREATED)
        
            except IntegrityError as e:
                return Response({
                    'success': False,
                    'message': '이미 존재하는 이메일입니다.',
                    'errors': {'email': ['이미 사용 중인 이메일입니다.']}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            except DatabaseError:
                return Response({
                    'success': False,
                    'message': '데이터베이스 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
                    'errors': {}
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        else:
            errors = serializer.errors if serializer.errors else {}
            if not isinstance(errors, dict):
                errors = {}

            return Response({
                'success': False,
                'message': '회원가입에 실패했습니다.',
                'errors': errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
    except (KeyError, TypeError):
        return Response({
            'success': False,
            'message': '요청 데이터가 올바르지 않습니다.',
            'errors': {}
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception:
        return Response({
            'success': False,
            'message': '서버 오류가 발생했습니다. 관리자에게 문의해주세요.',
            'errors': {}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@extend_schema(
    operation_id='user_login',
    summary="로그인",
    description="이메일과 비밀번호로 로그인하여 JWT 토큰을 발급받습니다.",
    request=LoginSerializer,
    responses={
        200: OpenApiResponse(
            response=dict,
            description="로그인 성공",
            examples=[
                OpenApiExample(
                    "로그인 성공",
                    value={
                        "success": True,
                        "message": "로그인이 완료되었습니다.",
                        "user": {
                            "id": 1,
                            "name": "홍길동",
                            "email": "hong@example.com",
                            "user_type": "trainer"
                        },
                        "tokens": {
                            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                        }
                    }
                )
            ]
        ),
        400: OpenApiResponse(description="로그인 실패")
    },
    tags=["인증"]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    # 로그인 api

    serializer = LoginSerializer(data=request.data)

    if serializer.is_valid():
        try:
            user = serializer.validated_data['user']
            tokens = get_tokens_for_user(user)

            return Response({
                'success': True,
                'message': '로그인이 완료 되었습니다.',
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'user_type': user.user_type
                }, 'tokens': tokens
            }, status=status.HTTP_200_OK)
        
        except TokenError:
            return Response({
                'success': False,
                'message': '토큰 생성 중 오류가 발생했습니다.',
                'errors': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except DatabaseError:
            return Response({
                'success': False,
                'message': '데이터베이스 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
                'errors': {}
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        except Exception:
            return Response({
                'success': False,
                'message': '서버 오류가 발생했습니다. 관리자에게 문의해주세요.',
                'errors': {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    errors = serializer.errors if serializer.errors else {}
    if not isinstance(errors, dict):
        errors = {}
    
    return Response({
        'success': False,
        'message': '로그인에 실패했습니다.',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)



@extend_schema(
    operation_id='user_logout',
    summary="로그아웃",
    description="Refresh token을 무효화하여 로그아웃합니다. 클라이언트에서는 저장된 토큰을 삭제해야 합니다.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'refresh': {
                    'type': 'string',
                    'description': '무효화할 refresh token'
                }
            },
            'required': ['refresh']
        }
    },
    responses={
        200: OpenApiResponse(
            response=dict,
            description="로그아웃 성공",
            examples=[
                OpenApiExample(
                    "로그아웃 성공",
                    value={
                        "success": True,
                        "message": "로그아웃이 완료되었습니다."
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            response=dict,
            description="잘못된 요청",
            examples=[
                OpenApiExample(
                    "refresh token 누락",
                    value={
                        "success": False,
                        "message": "Refresh token이 필요합니다.",
                        "errors": {"refresh": ["이 필드는 필수입니다."]}
                    }
                ),
                OpenApiExample(
                    "유효하지 않은 토큰",
                    value={
                        "success": False,
                        "message": "유효하지 않은 토큰입니다.",
                        "errors": {"refresh": ["토큰이 유효하지 않습니다."]}
                    }
                )
            ]
        ),
        401: OpenApiResponse(description="인증 실패")
    },
    tags=["인증"]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    # 로그아웃 API
    try:
        # refresh token 검증
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({
                'success': False,
                'message': 'Refresh token이 필요합니다.',
                'errors': {'refresh': ['이 필드는 필수입니다.']}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # refresh token 객체 생성 및 블랙리스트 추가
            token = RefreshToken(refresh_token)
            token.blacklist()  # 토큰을 블랙리스트에 추가
            
            return Response({
                'success': True,
                'message': '로그아웃이 완료되었습니다.'
            }, status=status.HTTP_200_OK)
            
        except (InvalidToken, TokenBackendError):
            return Response({
                'success': False,
                'message': '유효하지 않은 토큰입니다.',
                'errors': {'refresh': ['토큰이 유효하지 않습니다.']}
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except ValidationError as e:
            return Response({
                'success': False,
                'message': '토큰 형식이 올바르지 않습니다.',
                'errors': {'refresh': [str(e)]}
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except (KeyError, TypeError):
        return Response({
            'success': False,
            'message': '요청 데이터가 올바르지 않습니다.',
            'errors': {}
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except DatabaseError:
        return Response({
            'success': False,
            'message': '데이터베이스 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
            'errors': {}
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
    except Exception:
        return Response({
            'success': False,
            'message': '서버 오류가 발생했습니다. 관리자에게 문의해주세요.',
            'errors': {}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)