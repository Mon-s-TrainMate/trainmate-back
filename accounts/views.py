# accounts/views.py

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import SignupSerializer, LoginSerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

User = get_user_model()

# 사용자 JWT 토큰 생성
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    # 커스텀 claim 추가
    refresh['user_type'] = user.user_type
    refresh['name'] = user.name
    refresh['email'] = user.email

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

@extend_schema(
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
def signup_api(request):
    # 회원가입 api

    serializer = SignupSerializer(data=request.data)

    if serializer.is_valid():
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
    
    errors = serializer.errors if serializer.errors else {}
    if not isinstance(errors, dict):
        errors = {}
    print(errors)

    return Response({
        'success': False,
        'message': '회원가입에 실패했습니다.',
        'errors': errors
    }, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
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
        except Exception as e:
            return Response({
                'success': False,
                'message': '로그인 처리 중 오류가 발생하였습니다.',
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