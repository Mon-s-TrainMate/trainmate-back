# workouts/views.py

from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.openapi import OpenApiTypes
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models
from datetime import timedelta
from .models import DailyWorkout, ExerciseSet, WorkoutExercise, Exercise



@extend_schema(
    summary="회원 운동 기록 조회",
    description="특정 회원의 운동 기록을 운동별로 그룹화하여 조회합니다.",
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
    ],
    responses={
        200: OpenApiResponse(description="조회 성공"),
        401: OpenApiResponse(description="인증 필요"),
        500: OpenApiResponse(description="서버 오류")
    },
    tags=["운동 관리"]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def member_records_view(request, member_id):
    """회원의 운동 기록을 운동별로 그룹화하여 조회"""
    try:
        # 날짜 필터 (옵션)
        date_filter = request.GET.get('date')
        
        # WorkoutExercise 조회 (운동별로 그룹화된 단위)
        workout_exercises = WorkoutExercise.objects.filter(
            daily_workout__member_id=member_id
        ).select_related(
            'exercise',
            'daily_workout'
        ).prefetch_related('exercise_sets')
        
        # 날짜 필터 적용 (필요시)
        if date_filter:
            workout_exercises = workout_exercises.filter(
                daily_workout__workout_date=date_filter
            )
        
        # 운동 기록이 없는 경우 빈 배열 반환
        if not workout_exercises.exists():
            return Response({
                'success': True,
                'records': []
            }, status=status.HTTP_200_OK)
        
        # records 데이터 구성
        records_data = []
        for workout_exercise in workout_exercises:
            # 해당 운동의 모든 세트 조회
            exercise_sets = workout_exercise.exercise_sets.all()
            
            if exercise_sets.exists():
                records_data.append({
                    'id': workout_exercise.id,
                    'is_trainer': True,  # 트레이너가 등록한 기록
                    'exercise_name': workout_exercise.exercise.exercise_name,
                    'set_count': workout_exercise.total_sets,
                    'total_duration_sec': int(workout_exercise.total_duration.total_seconds()) if workout_exercise.total_duration else 0,
                    'calories_burned': workout_exercise.total_calories
                })
        
        # 최신순으로 정렬 (order_number 기준)
        records_data.sort(key=lambda x: x['id'], reverse=True)
        
        return Response({
            'success': True,
            'records': records_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"member_records_view 예외 발생: {type(e).__name__}: {e}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")
        return Response({
            'success': False,
            'message': f'운동 기록 조회 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@extend_schema(
    summary="운동 세트 등록",
    description="회원의 운동 세트를 등록합니다.",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "body_part": {"type": "string", "description": "운동 부위 (예: 등)"},
                "equipment": {"type": "string", "description": "운동 도구 (예: 머신)"},
                "exercise_name": {"type": "string", "description": "운동 이름 (예: 로잉 머신)"},
                "repetitions": {"type": "integer", "description": "횟수 (예: 15)"},
                "weight_kg": {"type": "number", "description": "중량 (예: 12.0)"},
                "duration_sec": {"type": "integer", "description": "시간 초 단위 (예: 390)"},
                "calories": {"type": "integer", "description": "칼로리 (예: 120)"},
            },
            "required": ["body_part", "equipment", "exercise_name", "repetitions", "weight_kg", "duration_sec", "calories"]
        }
    },
    responses={
        201: OpenApiResponse(description="운동 세트 등록 성공"),
        400: OpenApiResponse(description="유효성 검사 실패"),
        401: OpenApiResponse(description="인증 필요")
    },
    tags=["운동 관리"]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def workout_set_create_view(request, member_id):
    """운동 세트 등록"""
    try:
        data = request.data
        
        # 필수 필드 검증
        required_fields = ['body_part', 'equipment', 'exercise_name', 'repetitions', 'weight_kg', 'duration_sec', 'calories']
        for field in required_fields:
            if field not in data:
                return Response({
                    'success': False,
                    'message': f'{field} 필드가 필요합니다.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # 1. Exercise 찾기/생성
        exercise, created = Exercise.objects.get_or_create(
            exercise_name=data['exercise_name'],
            body_part=data['body_part'],
            equipment=data['equipment'],
            defaults={
                'measurement_unit': '회',
                'weight_unit': 'kg',
                'met_value': 6.0,
                'is_active': True
            }
        )
        
        # 2. 현재 로그인한 트레이너 정보 가져오기
        trainer = request.user  # 로그인한 트레이너
        
        # 3. 오늘 날짜 DailyWorkout 찾기/생성
        today = timezone.now().date()
        daily_workout, created = DailyWorkout.objects.get_or_create(
            member_id=member_id,
            trainer=trainer,
            workout_date=today,
            defaults={
                'total_duration': timedelta(0),
                'total_calories': 0,
                'is_completed': False
            }
        )
        
        # 4. WorkoutExercise 찾기/생성
        workout_exercise, we_created = WorkoutExercise.objects.get_or_create(
            daily_workout=daily_workout,
            exercise=exercise,
            defaults={
                'order_number': WorkoutExercise.objects.filter(daily_workout=daily_workout).count() + 1,
                'total_sets': 0,
                'total_duration': timedelta(0),
                'total_calories': 0
            }
        )
        
        # 5. 세트 번호 자동 계산
        last_set = ExerciseSet.objects.filter(
            workout_exercise=workout_exercise
        ).order_by('-set_number').first()
        
        next_set_number = (last_set.set_number + 1) if last_set else 1
        
        # 6. ExerciseSet 생성
        exercise_set = ExerciseSet.objects.create(
            workout_exercise=workout_exercise,
            set_number=next_set_number,
            repetitions=data['repetitions'],
            weight_kg=data['weight_kg'],
            duration=timedelta(seconds=data['duration_sec']),
            calories=data['calories']
        )
        
        # 7. WorkoutExercise 총합 업데이트
        exercise_sets = ExerciseSet.objects.filter(workout_exercise=workout_exercise)
        
        # 총 세트 수
        workout_exercise.total_sets = exercise_sets.count()
        
        # 총 시간 계산
        total_seconds = sum(
            int(es.duration.total_seconds()) for es in exercise_sets if es.duration
        )
        workout_exercise.total_duration = timedelta(seconds=total_seconds)
        
        # 총 칼로리 계산
        workout_exercise.total_calories = sum(es.calories for es in exercise_sets)
        workout_exercise.save()
        
        # 8. DailyWorkout 총합 업데이트
        all_workout_exercises = WorkoutExercise.objects.filter(daily_workout=daily_workout)
        
        # 일일 총 시간
        daily_total_seconds = sum(
            int(we.total_duration.total_seconds()) for we in all_workout_exercises if we.total_duration
        )
        daily_workout.total_duration = timedelta(seconds=daily_total_seconds)
        
        # 일일 총 칼로리
        daily_workout.total_calories = sum(we.total_calories for we in all_workout_exercises)
        daily_workout.save()
        
        # 응답 데이터 구성
        return Response({
            'success': True,
            'message': '운동 세트가 성공적으로 등록되었습니다.',
            'data': {
                'set_id': exercise_set.id,
                'exercise_name': exercise.exercise_name,
                'body_part': exercise.body_part,
                'equipment': exercise.equipment,
                'set_number': exercise_set.set_number,
                'repetitions': exercise_set.repetitions,
                'weight_kg': float(exercise_set.weight_kg),
                'duration_sec': int(exercise_set.duration.total_seconds()),
                'calories': exercise_set.calories,
                'workout_totals': {
                    'total_sets': workout_exercise.total_sets,
                    'total_duration_sec': int(workout_exercise.total_duration.total_seconds()),
                    'total_calories': workout_exercise.total_calories
                },
                'daily_totals': {
                    'total_duration_sec': int(daily_workout.total_duration.total_seconds()),
                    'total_calories': daily_workout.total_calories
                }
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        print(f"workout_set_create_view 예외 발생: {type(e).__name__}: {e}")
        import traceback
        print(f"상세 오류: {traceback.format_exc()}")
        return Response({
            'success': False,
            'message': '운동 세트 등록에 실패했습니다.',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)