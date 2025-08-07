# workouts/serializers.py

from rest_framework import serializers
from .models import DailyWorkout, WorkoutExercise, ExerciseSet, Exercise

class ExerciseInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        fields = ['id', 'exercise_name', 'body_part', 'equipment']



class ExerciseSetDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseSet
        fields = ['set_number', 'repetitions', 'weight_kg', 'duration', 'calories', 'completed_at']



class WorkoutExerciseDetailSerializer(serializers.ModelSerializer):
    exercise = ExerciseInfoSerializer(read_only=True)
    exercise_sets = ExerciseSetDetailSerializer(many=True, read_only=True)
    
    class Meta:
        model = WorkoutExercise
        fields = ['id', 'order_number', 'total_sets', 'total_duration', 'total_calories', 'exercise', 'exercise_sets']



class DailyWorkoutListSerializer(serializers.ModelSerializer):
    workout_exercises = WorkoutExerciseDetailSerializer(many=True, read_only=True)
    total_duration_display = serializers.SerializerMethodField()
    
    class Meta:
        model = DailyWorkout
        fields = ['id', 'workout_date', 'total_duration', 'total_duration_display', 'total_calories', 'is_completed', 'workout_exercises']
    
    def get_total_duration_display(self, obj):
        if obj.total_duration:
            total_seconds = int(obj.total_duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return "00:00:00"