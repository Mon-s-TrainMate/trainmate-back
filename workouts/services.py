# workouts/services.py

from .models import DailyWorkout

class WorkoutRecordService:
    @staticmethod
    def get_member_workout_records(member_id):
        # 회원의 모든 운동 기록을 조회하고 반환 
        try:
            daily_workouts = DailyWorkout.objects.filter(
                member_id=member_id
            ).select_related(
                'member', 'trainer'
            ).prefetch_related(
                'workout_exercises__exercise',
                'workout_exercises__exercise_sets'
            ).order_by('-workout_date', '-created_at')
            
            # 운동 기록 데이터 구성
            workout_records = []
            for workout in daily_workouts:
                # 총 운동시간 계산
                total_duration_display = "00:00:00"
                if workout.total_duration:
                    total_seconds = int(workout.total_duration.total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60
                    total_duration_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                
                # 운동 항목들 구성
                workout_exercises = []
                for workout_exercise in workout.workout_exercises.all():
                    # 운동별 총 시간 계산
                    exercise_duration_display = "00:00:00"
                    if workout_exercise.total_duration:
                        total_seconds = int(workout_exercise.total_duration.total_seconds())
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        seconds = total_seconds % 60
                        exercise_duration_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    
                    # 세트별 정보 구성
                    exercise_sets = []
                    for exercise_set in workout_exercise.exercise_sets.all():
                        set_duration_display = "00:00:00"
                        if exercise_set.duration:
                            total_seconds = int(exercise_set.duration.total_seconds())
                            hours = total_seconds // 3600
                            minutes = (total_seconds % 3600) // 60
                            seconds = total_seconds % 60
                            set_duration_display = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        
                        exercise_sets.append({
                            'set_number': exercise_set.set_number,
                            'repetitions': exercise_set.repetitions,
                            'weight_kg': float(exercise_set.weight_kg),
                            'duration': set_duration_display,
                            'calories': exercise_set.calories,
                            'completed_at': exercise_set.completed_at.isoformat() if exercise_set.completed_at else None
                        })
                    
                    workout_exercises.append({
                        'id': workout_exercise.id,
                        'order_number': workout_exercise.order_number,
                        'total_sets': workout_exercise.total_sets,
                        'total_duration': exercise_duration_display,
                        'total_calories': workout_exercise.total_calories,
                        'exercise': {
                            'id': workout_exercise.exercise.id,
                            'exercise_name': workout_exercise.exercise.exercise_name,
                            'body_part': workout_exercise.exercise.body_part,
                            'equipment': workout_exercise.exercise.equipment
                        },
                        'exercise_sets': exercise_sets
                    })
                
                workout_records.append({
                    'id': workout.id,
                    'workout_date': workout.workout_date.strftime('%Y-%m-%d'),
                    'workout_date_display': workout.workout_date.strftime('%m월 %d일'),
                    'total_duration': total_duration_display,
                    'total_calories': workout.total_calories,
                    'is_completed': workout.is_completed,
                    'workout_exercises': workout_exercises
                })
            
            return {
                'workout_records': workout_records,
                'total_workouts': len(workout_records),
                'has_records': len(workout_records) > 0
            }
            
        except Exception as e:
            return {
                'workout_records': [],
                'total_workouts': 0,
                'has_records': False
            }