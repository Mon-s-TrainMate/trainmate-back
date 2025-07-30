# accounts/views.py

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import SignupSerializer, LoginSerializer

User = get_user_model()

@api_view(['POST'])
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
                'name': user.first_name,
                'email': user.email,
                'user_type': user.user_type
            }
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'success': False,
        'message': '회원가입에 실패했습니다.',
        'error': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

# 사용자 JWT 토큰 생성
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    # 커스텀 claim 추가
    refresh['user_type'] = user.user_type
    refresh['name'] = user.name

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

@api_view(['POST'])
def login_api(request):
    # 로그인 api

    serializer = LoginSerializer(data=request.data)

    if serializer.is_valid():
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
    
    return Response({
        'success': False,
        'message': '로그인에 실패했습니다.',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)