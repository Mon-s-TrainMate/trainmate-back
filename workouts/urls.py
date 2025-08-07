# workouts/urls.py

from django.urls import path
# from .views import WorkoutRecordCreateView, MemberRecordsView
from .views import MemberRecordsView

urlpatterns = [
    # 운동 기록 등록
    # path('<int:member_id>/', WorkoutRecordCreateView.as_view(), name='workout-record-create'),
    
    # 회원 운동 기록 조회 (프론트엔드가 호출하는 URL)
    path('<int:member_id>/records/', MemberRecordsView.as_view(), name='member-records'),
]