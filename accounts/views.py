# accounts/views.py

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import SignupSerializer

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