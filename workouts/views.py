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
    # 회원의 운동 기록을 운동별로 그룹화하여 조회 
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

        daily_total_seconds = 0
        daily_total_calories = 0

        for workout_exercise in workout_exercises:
            # 해당 운동의 모든 세트 조회
            exercise_sets = workout_exercise.exercise_sets.all()
            
            if exercise_sets.exists():
                records_data.append({
                    'id': workout_exercise.id,
                    'is_trainer': workout_exercise.daily_workout.member == workout_exercise.daily_workout.trainer,
                    'exercise_name': workout_exercise.exercise.exercise_name,
                    'set_count': workout_exercise.total_sets,
                    'total_duration_sec': int(workout_exercise.total_duration.total_seconds()) if workout_exercise.total_duration else 0,
                    'calories_burned': workout_exercise.total_calories
                })

                daily_total_seconds += int(workout_exercise.total_duration.total_seconds()) if workout_exercise.total_duration else 0
                daily_total_calories += workout_exercise.total_calories
        
        # 최신순으로 정렬 (order_number 기준)
        records_data.sort(key=lambda x: x['id'], reverse=True)
        
        return Response({
            'success': True,
            'records': records_data,
            'daily_summary': {
                'total_duration_sec': daily_total_seconds,
                'total_calories': daily_total_calories
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
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
    # 운동 세트 등록 
    try:
        data = request.data
        current_user = request.user
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if current_user.user_type == 'trainer':
            if current_user.id == member_id:
                target_user = current_user
                is_trainer_workout = True
            else:
                try:
                    target_user = User.objects.get(id=member_id, user_type='member')
                    is_trainer_workout = False
                except User.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': '해당 회원을 찾을 수 없습니다.'
                    }, status=status.HTTP_404_NOT_FOUND)
        elif current_user.user_type == 'member':
            if current_user.id != member_id:
                return Response({
                    'success': False,
                    'message': '본인의 운동 기록만 등록할 수 있습니다.'
                }, status=status.HTTP_403_FORBIDDEN)
            target_user = current_user
            is_trainer_workout = False
        else:
            return Response({
                'success': False,
                'message': '유효하지 않은 사용자 타입입니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 필수 필드 검증
        required_fields = ['body_part', 'equipment', 'exercise_name', 'repetitions', 'weight_kg', 'duration_sec', 'calories']
        for field in required_fields:
            if field not in data:
                return Response({
                    'success': False,
                    'message': f'{field} 필드가 필요합니다.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # 1. Exercise 찾기/생성 (기존과 동일)
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
        
        # 2. 등록하는 트레이너
        from members.models import Trainer
        try:
            registering_trainer = Trainer.objects.get(user_ptr_id=current_user.id)
        except Trainer.DoesNotExist:
            return Response({
                'success': False,
                'message': '트레이너 정보를 찾을 수 없습니다.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 3. 오늘 날짜 DailyWorkout 찾기/생성
        today = timezone.now().date()
        daily_workout, created = DailyWorkout.objects.get_or_create(
            member=target_user,          # ✅ User 인스턴스 바로 사용!
            trainer=registering_trainer,
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
                'set_number': exercise_set.set_number,
                'exercise_name': exercise.exercise_name,
                'workout_exercise_id': workout_exercise.id
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': '운동 세트 등록에 실패했습니다.',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# 운동 목록 조회
@extend_schema(
    summary="운동 목록 조회",
    description="등록 가능한 운동 목록을 조회합니다.",
    parameters=[
        OpenApiParameter(
            name='body_part',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='운동 부위별 필터링',
            required=False
        )
    ],
    responses={
        200: OpenApiResponse(description="조회 성공"),
        401: OpenApiResponse(description="인증 필요")
    }, tags=["운동 관리"]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def exercise_list_view(request):
    # 운동 목록 조회 API
    try:
        exercises = Exercise.objects.filter(is_active=True)

        # 운동 부위별 필터링
        body_part = request.GET.get('body_part')
        if body_part:
            exercises = exercises.filter(body_part=body_part)

        # 운동 부위별 그룹화
        from collections import defaultdict
        grouped_exercises = defaultdict(list)

        for exercise in exercises:
            grouped_exercises[exercise.body_part].append({
                'id': exercise.id,
                'exercise_name': exercise.exercise_name,
                'equipment': exercise.equipment,
                'measurement_unit': exercise.measurement_unit,
                'weight_unit': exercise.weight_unit
            })
        return Response({
            'success': True,
            'data': dict(grouped_exercises)
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'success': False,
            'message': f'운동 목록 조회 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# 운동 세트 목록 조회
@extend_schema(
    summary="특정 운동의 세트 목록 조회",
    description="특정 운동의 모든 세트 목록을 조회합니다",
    tags=["운동 관리"]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def workout_exercise_sets_view(request, member_id, workout_exercise_id):
    try:
        workout_exercise = get_object_or_404(
            WorkoutExercise.objects.select_related('exercise'),
            id=workout_exercise_id,
            daily_workout__member_id=member_id
        )

        # 해당 운동의 모든 세트 조회
        exercise_sets = ExerciseSet.objects.filter(
            workout_exercise=workout_exercise
        ).order_by('set_number')

        # 세트 목록 구성
        sets_data = []
        for es in exercise_sets:
            duration_minutes = int(es.duration.total_seconds()) // 60
            duration_seconds = int(es.duration.total_seconds()) % 60
            sets_data.append({
                'set_id': es.id,
                'set_number': es.set_number,
                'repetitions': es.repetitions,
                'weight_kg': float(es.weight_kg),
                'duration_sec': int(es.duration.total_seconds()),
                'duration_display': f"{duration_minutes:02d}:{duration_seconds:02d}",
                'calories': es.calories,
                'is_completed': True,
                'completed_at': es.completed_at.strftime('%H:%M:%S')
            })

        # 총 시간 표시용 포맷 추가
        total_duration_minutes = int(workout_exercise.total_duration.total_seconds()) // 60
        total_duration_seconds = int(workout_exercise.total_duration.total_seconds()) % 60
        total_duration_display = f"{total_duration_minutes:02d}:{total_duration_seconds:02d}"
        
        return Response({
            'success': True,
            'data':{
                'workout_exercise_id': workout_exercise.id,
                'exercise_name': workout_exercise.exercise.exercise_name,
                'body_part': workout_exercise.exercise.body_part,
                'total_sets': workout_exercise.total_sets,
                'total_duration_sec': int(workout_exercise.total_duration.total_seconds()),
                'total_duration_display': total_duration_display,
                'total_calories': workout_exercise.total_calories,
                'sets': sets_data
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'success': False,
            'message': '세트 목록 조회 중 오류가 발생했습니다.',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@extend_schema(
    methods=['GET'],
    summary="개별 세트 상세 조회",
    description="특정 세트의 상세 정보를 조회합니다.",
    tags=["운동 관리"]
)
@extend_schema(
    methods=['PATCH'],
    summary="개별 세트 수정",
    description="특정 세트의 정보를 수정합니다.",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "repetitions": {"type": "integer", "description": "횟수"},
                "weight_kg": {"type": "number", "description": "중량"},
                "duration_sec": {"type": "integer", "description": "시간 초 단위"},
                "calories": {"type": "integer", "description": "칼로리"},
            }
        }
    },
    tags=["운동 관리"]
)
@extend_schema(
    methods=['DELETE'],
    summary="개별 세트 삭제",
    description="특정 세트를 삭제합니다.",
    responses={
        200: OpenApiResponse(description="세트 삭제 성공"),
        400: OpenApiResponse(description="잘못된 요청"),
        401: OpenApiResponse(description="인증 필요"),
        403: OpenApiResponse(description="권한 없음"),
        404: OpenApiResponse(description="세트를 찾을 수 없음"),
        500: OpenApiResponse(description="서버 내부 오류")
    },
    tags=["운동 관리"]
)
@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def exercise_set_view(request, member_id, workout_exercise_id, set_id):
    if request.method == 'GET':
        return exercise_set_detail(request, member_id, workout_exercise_id, set_id)
    
    elif request.method == 'PATCH':
        return exercise_set_update(request, member_id, workout_exercise_id, set_id)
    
    elif request.method == 'DELETE':  # 추가됨: DELETE 메서드 처리
        return exercise_set_delete(request, member_id, workout_exercise_id, set_id)



def exercise_set_detail(request, member_id, workout_exercise_id, set_id):
    try:
        exercise_set = get_object_or_404(
            ExerciseSet.objects.select_related(
                'workout_exercise__exercise',
                'workout_exercise__daily_workout'
            ),
            id=set_id,
            workout_exercise_id=workout_exercise_id,
            workout_exercise__daily_workout__member_id=member_id
        )

        duration_minutes = int(exercise_set.duration.total_seconds()) // 60
        duration_seconds = int(exercise_set.duration.total_seconds()) % 60

        return Response({
            'success': True,
            'data': {
                'set_id': exercise_set.id,
                'set_number': exercise_set.set_number,
                'exercise_name': exercise_set.workout_exercise.exercise.exercise_name,
                'repetitions': exercise_set.repetitions,
                'weight_kg': float(exercise_set.weight_kg),
                'duration_sec': int(exercise_set.duration.total_seconds()),
                'duration_display': f"{duration_minutes:02d}:{duration_seconds:02d}",
                'calories': exercise_set.calories,
                'is_completed': True,
                'completed_at': exercise_set.completed_at.strftime('%H:%M:%S')
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'success': False,
            'message': '세트 상세 조회 중 오류가 발생했습니다.',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



def exercise_set_update(request, member_id, workout_exercise_id, set_id):
    try:
        current_user = request.user

        from django.contrib.auth import get_user_model
        User = get_user_model()

        if current_user.user_type == 'trainer':
            # 트레이너는 본인이거나 담당 회원의 기록을 수정 가능
            if current_user.id != member_id:
                try:
                    target_user = User.objects.get(id=member_id, user_type='member')
                except User.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': '해당 회원을 찾을 수 없습니다.'
                    }, status=status.HTTP_404_NOT_FOUND)
        elif current_user.user_type == 'member':
            # 회원은 본인의 기록만 수정 가능
            if current_user.id != member_id:
                return Response({
                    'success': False,
                    'message': '본인의 운동 기록만 수정할 수 있습니다.'
                }, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({
                'success': False,
                'message': '유효하지 않은 사용자 타입입니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 세트 조회 (추가됨: 세트 존재 여부 확인)
        exercise_set = get_object_or_404(
            ExerciseSet.objects.select_related(
                'workout_exercise__exercise',
                'workout_exercise__daily_workout'
            ),
            id=set_id,
            workout_exercise_id=workout_exercise_id,
            workout_exercise__daily_workout__member_id=member_id
        )

        data = request.data
        updated_fields = []

        if 'repetitions' in data:
            exercise_set.repetitions = data['repetitions']
            updated_fields.append('repetitions')
            
        if 'weight_kg' in data:
            exercise_set.weight_kg = data['weight_kg']
            updated_fields.append('weight_kg')
            
        if 'duration_sec' in data:
            exercise_set.duration = timedelta(seconds=data['duration_sec'])
            updated_fields.append('duration_sec')
            
        if 'calories' in data:
            exercise_set.calories = data['calories']
            updated_fields.append('calories')

        if not updated_fields:
            return Response({
                'success': False,
                'message': '수정할 필드가 없습니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        exercise_set.save()

        workout_exercise = exercise_set.workout_exercise
        exercise_sets = ExerciseSet.objects.filter(workout_exercise=workout_exercise)

        # 총 세트 수
        workout_exercise.total_sets = exercise_sets.count()

        # 총 시간 재계산
        total_seconds = sum(
            int(es.duration.total_seconds()) for es in exercise_sets if es.duration
        )
        workout_exercise.total_duration = timedelta(seconds=total_seconds)

        # 총 칼로리 재계산
        workout_exercise.total_calories = sum(es.calories for es in exercise_sets)
        workout_exercise.save()

        # DailyWorkout 총합 재계산
        daily_workout = workout_exercise.daily_workout
        all_workout_exercises = WorkoutExercise.objects.filter(daily_workout=daily_workout)

        # 일일 총 시간 재계산
        daily_total_seconds = sum(
            int(we.total_duration.total_seconds()) for we in all_workout_exercises if we.total_duration
        )
        daily_workout.total_duration = timedelta(seconds=daily_total_seconds)

        # 일일 총 칼로리 재계산
        daily_workout.total_calories = sum(we.total_calories for we in all_workout_exercises)
        daily_workout.save()

        duration_minutes = int(exercise_set.duration.total_seconds()) // 60
        duration_seconds = int(exercise_set.duration.total_seconds()) % 60

        return Response({
            'success': True,
            'message': '세트가 성공적으로 수정되었습니다.',
            'data': {
                'set_id': exercise_set.id,
                'set_number': exercise_set.set_number,
                'exercise_name': exercise_set.workout_exercise.exercise.exercise_name,
                'repetitions': exercise_set.repetitions,
                'weight_kg': float(exercise_set.weight_kg),
                'duration_sec': int(exercise_set.duration.total_seconds()),
                'duration_display': f"{duration_minutes:02d}:{duration_seconds:02d}",
                'calories': exercise_set.calories,
                'updated_fields': updated_fields  # 추가됨: 수정된 필드 목록
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': '세트 수정 중 오류가 발생했습니다.',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



def exercise_set_delete(request, member_id, workout_exercise_id, set_id):
    try:
        current_user = request.user

        # 권한 검증 
        from django.contrib.auth import get_user_model
        from django.db import DatabaseError, IntegrityError
        
        User = get_user_model()

        if current_user.user_type == 'trainer':
            if current_user.id != member_id:
                try:
                    target_user = User.objects.get(id=member_id, user_type='member')
                except User.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': '해당 회원을 찾을 수 없습니다.'
                    }, status=status.HTTP_404_NOT_FOUND)
                except DatabaseError:
                    return Response({
                        'success': False,
                        'message': '데이터베이스 연결 오류가 발생했습니다.'
                    }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        elif current_user.user_type == 'member':
            if current_user.id != member_id:
                return Response({
                    'success': False,
                    'message': '본인의 운동 기록만 삭제할 수 있습니다.'
                }, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({
                'success': False,
                'message': '유효하지 않은 사용자 타입입니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 세트 조회
        try:
            exercise_set = get_object_or_404(
                ExerciseSet.objects.select_related(
                    'workout_exercise__exercise',
                    'workout_exercise__daily_workout'
                ),
                id=set_id,
                workout_exercise_id=workout_exercise_id,
                workout_exercise__daily_workout__member_id=member_id
            )
        except Exception as e:
            return Response({
                'success': False,
                'message': '세트를 찾을 수 없습니다.'
            }, status=status.HTTP_404_NOT_FOUND)

        # 마지막 세트인지 확인
        workout_exercise = exercise_set.workout_exercise
        remaining_sets = ExerciseSet.objects.filter(workout_exercise=workout_exercise)
        
        if remaining_sets.count() == 1:
            return Response({
                'success': False,
                'message': '운동의 마지막 세트는 삭제할 수 없습니다. 운동 전체를 삭제해주세요.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 삭제할 세트 정보 백업 (응답용)
        deleted_set_info = {
            'set_id': exercise_set.id,
            'set_number': exercise_set.set_number,
            'exercise_name': exercise_set.workout_exercise.exercise.exercise_name
        }

        # 세트 삭제
        try:
            exercise_set.delete()
            
        except IntegrityError as e:
            return Response({
                'success': False,
                'message': '데이터 무결성 제약으로 인해 삭제할 수 없습니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except DatabaseError as e:
            return Response({
                'success': False,
                'message': '데이터베이스 연결 오류가 발생했습니다.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 남은 세트들의 번호 재정렬
        try:
            remaining_sets = ExerciseSet.objects.filter(
                workout_exercise=workout_exercise
            ).order_by('set_number')
            
            for index, es in enumerate(remaining_sets, 1):
                if es.set_number != index:
                    es.set_number = index
                    es.save()
                    
        except DatabaseError as e:
            return Response({
                'success': False,
                'message': '세트 번호 재정렬 중 오류가 발생했습니다.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # WorkoutExercise 총합 재계산
        try:
            exercise_sets = ExerciseSet.objects.filter(workout_exercise=workout_exercise)
            
            workout_exercise.total_sets = exercise_sets.count()
            
            total_seconds = sum(
                int(es.duration.total_seconds()) for es in exercise_sets if es.duration
            )
            workout_exercise.total_duration = timedelta(seconds=total_seconds)
            
            workout_exercise.total_calories = sum(es.calories for es in exercise_sets)
            workout_exercise.save()

            # DailyWorkout 총합 재계산
            daily_workout = workout_exercise.daily_workout
            all_workout_exercises = WorkoutExercise.objects.filter(daily_workout=daily_workout)
            
            daily_total_seconds = sum(
                int(we.total_duration.total_seconds()) for we in all_workout_exercises if we.total_duration
            )
            daily_workout.total_duration = timedelta(seconds=daily_total_seconds)
            daily_workout.total_calories = sum(we.total_calories for we in all_workout_exercises)
            daily_workout.save()

        except DatabaseError as e:
            return Response({
                'success': False,
                'message': '총합 재계산 중 데이터베이스 오류가 발생했습니다.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 성공 응답 (추가됨)
        return Response({
            'success': True,
            'message': '세트가 성공적으로 삭제되었습니다.',
            'data': deleted_set_info
        }, status=status.HTTP_200_OK)

    except AttributeError as e:
        return Response({
            'success': False,
            'message': '객체 속성에 접근할 수 없습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': '세트 삭제 중 예상치 못한 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@extend_schema(
    summary="기존 운동에 세트 추가",
    description="특정 운동에 새로운 세트를 추가합니다.",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "repetitions": {"type": "integer", "description": "횟수 (예: 15)"},
                "weight_kg": {"type": "number", "description": "중량 (예: 12.0)"},
                "duration_sec": {"type": "integer", "description": "시간 초 단위 (예: 390)"},
                "calories": {"type": "integer", "description": "칼로리 (예: 120)"},
            },
            "required": ["repetitions", "weight_kg", "duration_sec", "calories"]
        }
    },
    responses={
        201: OpenApiResponse(description="세트 추가 성공"),
        400: OpenApiResponse(description="유효성 검사 실패"),
        401: OpenApiResponse(description="인증 필요"),
        403: OpenApiResponse(description="권한 없음"),
        404: OpenApiResponse(description="운동을 찾을 수 없음"),
        500: OpenApiResponse(description="서버 내부 오류")
    },
    tags=["운동 관리"]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def exercise_set_create_view(request, member_id, workout_exercise_id):  # 추가됨: 기존 운동에 세트 추가
    try:
        current_user = request.user
        data = request.data

        # 권한 검증
        from django.contrib.auth import get_user_model
        from django.db import DatabaseError, IntegrityError
        from django.core.exceptions import ValidationError as DjangoValidationError
        
        User = get_user_model()

        if current_user.user_type == 'trainer':
            if current_user.id != member_id:
                try:
                    target_user = User.objects.get(id=member_id, user_type='member')
                except User.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': '해당 회원을 찾을 수 없습니다.'
                    }, status=status.HTTP_404_NOT_FOUND)
                except DatabaseError:
                    return Response({
                        'success': False,
                        'message': '데이터베이스 연결 오류가 발생했습니다.'
                    }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        elif current_user.user_type == 'member':
            if current_user.id != member_id:
                return Response({
                    'success': False,
                    'message': '본인의 운동 기록만 추가할 수 있습니다.'
                }, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({
                'success': False,
                'message': '유효하지 않은 사용자 타입입니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 필수 필드 검증
        required_fields = ['repetitions', 'weight_kg', 'duration_sec', 'calories']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return Response({
                'success': False,
                'message': f'필수 필드가 누락되었습니다: {", ".join(missing_fields)}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 데이터 타입 검증
        try:
            repetitions = int(data['repetitions'])
            weight_kg = float(data['weight_kg'])
            duration_sec = int(data['duration_sec'])
            calories = int(data['calories'])
            
            if repetitions <= 0 or weight_kg < 0 or duration_sec <= 0 or calories < 0:
                raise ValueError("값은 양수여야 합니다.")
                
        except (ValueError, TypeError) as e:
            return Response({
                'success': False,
                'message': '입력값의 형식이 올바르지 않습니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # WorkoutExercise 조회
        try:
            workout_exercise = get_object_or_404(
                WorkoutExercise.objects.select_related('daily_workout'),
                id=workout_exercise_id,
                daily_workout__member_id=member_id
            )
        except Exception as e:  # 수정됨: 구체적 예외 처리
            return Response({
                'success': False,
                'message': '운동 정보를 찾을 수 없습니다.'
            }, status=status.HTTP_404_NOT_FOUND)

        # 세트 번호 자동 계산
        try:
            last_set = ExerciseSet.objects.filter(
                workout_exercise=workout_exercise
            ).order_by('-set_number').first()
            
            next_set_number = (last_set.set_number + 1) if last_set else 1

            # ExerciseSet 생성
            exercise_set = ExerciseSet.objects.create(
                workout_exercise=workout_exercise,
                set_number=next_set_number,
                repetitions=repetitions,
                weight_kg=weight_kg,
                duration=timedelta(seconds=duration_sec),
                calories=calories
            )

        except IntegrityError as e:
            return Response({
                'success': False,
                'message': '데이터 무결성 오류가 발생했습니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except DjangoValidationError as e:
            return Response({
                'success': False,
                'message': '입력값 유효성 검사에 실패했습니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # WorkoutExercise 총합 업데이트
        try:
            exercise_sets = ExerciseSet.objects.filter(workout_exercise=workout_exercise)
            
            workout_exercise.total_sets = exercise_sets.count()
            
            total_seconds = sum(
                int(es.duration.total_seconds()) for es in exercise_sets if es.duration
            )
            workout_exercise.total_duration = timedelta(seconds=total_seconds)
            
            workout_exercise.total_calories = sum(es.calories for es in exercise_sets)
            workout_exercise.save()

            # DailyWorkout 총합 업데이트
            daily_workout = workout_exercise.daily_workout
            all_workout_exercises = WorkoutExercise.objects.filter(daily_workout=daily_workout)
            
            daily_total_seconds = sum(
                int(we.total_duration.total_seconds()) for we in all_workout_exercises if we.total_duration
            )
            daily_workout.total_duration = timedelta(seconds=daily_total_seconds)
            daily_workout.total_calories = sum(we.total_calories for we in all_workout_exercises)
            daily_workout.save()

        except DatabaseError as e:
            return Response({
                'success': False,
                'message': '총합 계산 중 데이터베이스 오류가 발생했습니다.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 성공 응답
        duration_minutes = int(exercise_set.duration.total_seconds()) // 60
        duration_seconds = int(exercise_set.duration.total_seconds()) % 60

        return Response({
            'success': True,
            'message': '세트가 성공적으로 추가되었습니다.',
            'data': {
                'set_id': exercise_set.id,
                'set_number': exercise_set.set_number,
                'exercise_name': workout_exercise.exercise.exercise_name,
                'repetitions': exercise_set.repetitions,
                'weight_kg': float(exercise_set.weight_kg),
                'duration_sec': int(exercise_set.duration.total_seconds()),
                'duration_display': f"{duration_minutes:02d}:{duration_seconds:02d}",
                'calories': exercise_set.calories,
                'workout_exercise_id': workout_exercise.id
            }
        }, status=status.HTTP_201_CREATED)

    except KeyError as e:
        return Response({
            'success': False,
            'message': f'필수 필드가 누락되었습니다: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except AttributeError as e:
        return Response({
            'success': False,
            'message': '객체 속성에 접근할 수 없습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:  # 수정됨: 최후의 예외 처리
        return Response({
            'success': False,
            'message': '세트 추가 중 예상치 못한 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)