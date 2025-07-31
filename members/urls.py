# members/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # 내 프로필 조회/수정
    path('profile/', views.get_my_profile, name='my_profile'),
    path('profile/', views.update_my_profile, name='update_profile'),
    
    # 다른 사용자 프로필 조회
    path('profile/<int:user_id>/', views.get_user_profile, name='user_profile'),
]