# members/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # 내 프로필 조회/수정
    # /api/members/profile
    path('profile/', views.my_profile_view, name='my_profile'),
    
    # 다른 사용자 프로필 조회
    # /api/members/profile/123
    path('profile/<int:user_id>/', views.get_user_profile, name='user_profile'),

    # 트레이너의 회원 목록 조회
    # /api/members
    path('', views.trainer_member_list, name='trainer_member_list'),

    # 회원/트레이너 상세 정보 조회
    # /api/members/123/
    path('<int:member_id>/', views.member_detail, name='member-detail'),
]