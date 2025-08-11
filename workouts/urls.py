# workouts/urls.py

from django.urls import path
# from .views import WorkoutRecordCreateView, MemberRecordsView
from .views import member_records_view, workout_set_create_view, exercise_list_view

urlpatterns = [
    # 운동 세트 등록
    path('<int:member_id>/workout-sets/', workout_set_create_view, name='workout-set-create'),
    
    # 회원 운동 기록 조회
    path('<int:member_id>/records/', member_records_view, name='member-records'),

    # 운동 목록 조회 (새로 추가 - 프론트엔드에서 운동 선택할 때 사용)
    path('exercises/', exercise_list_view, name='exercise-list'),
]