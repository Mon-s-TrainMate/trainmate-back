# workouts/views.py

from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from django.shortcuts import get_object_or_404
from .models import DailyWorkout, ExerciseSet



class MemberRecordsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def dispatch(self, request, *args, **kwargs):
        """모든 요청에 대해 JSON 응답 보장"""
        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            # 예외 발생 시 JSON 응답 강제
            return Response({
                'error': 'INTERNAL_SERVER_ERROR',
                'message': f'서버 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def handle_exception(self, exc):
        """인증 실패나 권한 오류 시 JSON 응답"""
        if hasattr(exc, 'status_code'):
            if exc.status_code == 401:
                return Response({
                    'error': 'UNAUTHORIZED',
                    'message': '인증이 필요합니다.'
                }, status=status.HTTP_401_UNAUTHORIZED)
            elif exc.status_code == 403:
                return Response({
                    'error': 'FORBIDDEN',
                    'message': '권한이 없습니다.'
                }, status=status.HTTP_403_FORBIDDEN)
        
        return super().handle_exception(exc)
    
    @extend_schema(
        summary="회원 운동 기록 조회",
        description="특정 회원의 운동 기록을 세트 단위로 조회합니다.",
        parameters=[
            OpenApiParameter(
                name='member_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='조회할 회원의 ID',
                required=True
            ),
            OpenApiParameter(
                name='date',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='조회할 날짜 (YYYY-MM-DD)',
                required=False
            )
        ]
    )
    def get(self, request, member_id):
        """회원의 운동 기록을 세트 단위로 조회 (프론트엔드 기대 형식)"""
        try:
            # 날짜 필터 (옵션)
            date_filter = request.GET.get('date')
            
            # 모든 세트 데이터 조회
            exercise_sets = ExerciseSet.objects.filter(
                workout_exercise__daily_workout__member_id=member_id
            ).select_related(
                'workout_exercise__exercise',
                'workout_exercise__daily_workout'
            ).order_by('-completed_at')
            
            # 날짜 필터 적용 (필요시)
            if date_filter:
                exercise_sets = exercise_sets.filter(
                    workout_exercise__daily_workout__workout_date=date_filter
                )
            
            # 운동 기록이 없는 경우 빈 배열 반환
            if not exercise_sets.exists():
                return Response({
                    'success': True,
                    'sets': []
                }, status=status.HTTP_200_OK)
            
            # 응답 데이터 구성 (프론트엔드 기대 형식에 맞춤)
            sets_data = []
            for exercise_set in exercise_sets:
                # 총 운동시간을 초 단위로 변환
                total_duration_sec = 0
                if exercise_set.duration:
                    total_duration_sec = int(exercise_set.duration.total_seconds())
                
                sets_data.append({
                    'set_id': exercise_set.id,
                    'is_trainer': True,  # 트레이너가 등록한 기록
                    'exercise_name': exercise_set.workout_exercise.exercise.exercise_name,
                    'set_count': exercise_set.set_number,
                    'total_duration_sec': total_duration_sec,
                    'calories_burned': exercise_set.calories
                })
            
            return Response({
                'success': True,
                'sets': sets_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"MemberRecordListView 예외 발생: {type(e).__name__}: {e}")
            import traceback
            print(f"상세 오류: {traceback.format_exc()}")
            return Response({
                'error': 'INTERNAL_SERVER_ERROR',
                'message': f'운동 기록 조회 중 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)