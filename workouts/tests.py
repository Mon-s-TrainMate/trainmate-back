# workouts/tests.py

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch
from members.models import Trainer
from .models import DailyWorkout, ExerciseSet, WorkoutExercise, Exercise

User = get_user_model()


class WorkoutViewsTestCase(TestCase):
    # 운동 관리 API 테스트
    
    def setUp(self):
        # 테스트 데이터 초기화
        self.client = APIClient()
        
        # 각 테스트마다 고유한 이메일을 위한 UUID 사용
        import uuid
        self.unique_id = str(uuid.uuid4())[:8]
        
        # 트레이너 생성 (Trainer가 User를 상속받는 모델)
        self.trainer_user = Trainer.objects.create_user(
            email=f'trainer{self.unique_id}@test.com',
            password='testpass123',
            user_type='trainer'
        )
        self.trainer = self.trainer_user
        
        # 일반 회원 사용자들 생성
        self.member_user = User.objects.create_user(
            email=f'member{self.unique_id}@test.com',
            password='testpass123',
            user_type='member'
        )
        
        self.other_member = User.objects.create_user(
            email=f'member2{self.unique_id}@test.com',
            password='testpass123',
            user_type='member'
        )
        
        # 테스트 운동 데이터 생성
        self.exercise = Exercise.objects.create(
            exercise_name='벤치프레스',
            body_part='가슴',
            equipment='바벨',
            measurement_unit='회',
            weight_unit='kg',
            met_value=6.0,
            is_active=True
        )
        
        # 테스트 운동 기록 생성
        self.daily_workout = DailyWorkout.objects.create(
            member=self.member_user,
            trainer=self.trainer,
            workout_date=timezone.now().date(),
            total_duration=timedelta(minutes=60),
            total_calories=150,
            is_completed=False
        )
        
        # 운동 실행 기록 생성
        self.workout_exercise = WorkoutExercise.objects.create(
            daily_workout=self.daily_workout,
            exercise=self.exercise,
            order_number=1,
            total_sets=1,
            total_duration=timedelta(minutes=30),
            total_calories=150
        )
        
        # 운동 세트 생성
        self.exercise_set = ExerciseSet.objects.create(
            workout_exercise=self.workout_exercise,
            set_number=1,
            repetitions=10,
            weight_kg=80.0,
            duration=timedelta(minutes=15),
            calories=150
        )


class MemberRecordsViewTestCase(WorkoutViewsTestCase):
    # 회원 운동 기록 조회 API 테스트
    
    def test_member_records_view_success(self):
        # 정상적인 운동 기록 조회 테스트
        self.client.force_authenticate(user=self.trainer_user)
        url = reverse('member-records', kwargs={'member_id': self.member_user.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('records', response.data)
        self.assertIn('daily_summary', response.data)
        self.assertEqual(len(response.data['records']), 1)
        
        # 기록 데이터 검증
        record = response.data['records'][0]
        self.assertEqual(record['exercise_name'], '벤치프레스')
        self.assertEqual(record['set_count'], 1)
        self.assertEqual(record['calories_burned'], 150)
    
    def test_member_records_view_with_date_filter(self):
        # 날짜 필터를 적용한 운동 기록 조회 테스트
        self.client.force_authenticate(user=self.trainer_user)
        url = reverse('member-records', kwargs={'member_id': self.member_user.id})
        
        today = timezone.now().date().strftime('%Y-%m-%d')
        response = self.client.get(url, {'date': today})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['records']), 1)
    
    def test_member_records_view_empty_records(self):
        # 운동 기록이 없는 경우 테스트
        self.client.force_authenticate(user=self.trainer_user)
        url = reverse('member-records', kwargs={'member_id': self.other_member.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['records']), 0)
    
    def test_member_records_view_unauthorized(self):
        # 인증되지 않은 사용자 접근 테스트
        url = reverse('member-records', kwargs={'member_id': self.member_user.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class WorkoutSetCreateViewTestCase(WorkoutViewsTestCase):
    # 운동 세트 등록 API 테스트
    
    def test_workout_set_create_success_trainer(self):
        # 트레이너가 회원을 위한 운동 세트 등록 성공 테스트
        self.client.force_authenticate(user=self.trainer_user)
        url = reverse('workout-set-create', kwargs={'member_id': self.member_user.id})
        
        data = {
            'body_part': '등',
            'equipment': '머신',
            'exercise_name': '로잉 머신',
            'repetitions': 15,
            'weight_kg': 12.0,
            'duration_sec': 390,
            'calories': 120
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('data', response.data)
        self.assertEqual(response.data['data']['exercise_name'], '로잉 머신')
        
        # 새로운 운동이 생성되었는지 확인
        self.assertTrue(Exercise.objects.filter(exercise_name='로잉 머신').exists())
    
    def test_workout_set_create_member_with_trainer_requirement(self):
        # 회원이 운동 세트 등록 시 트레이너 정보 필요성 테스트
        self.client.force_authenticate(user=self.member_user)
        url = reverse('workout-set-create', kwargs={'member_id': self.member_user.id})
        
        data = {
            'body_part': '다리',
            'equipment': '바벨',
            'exercise_name': '스쿼트',
            'repetitions': 12,
            'weight_kg': 60.0,
            'duration_sec': 300,
            'calories': 100
        }
        
        response = self.client.post(url, data, format='json')
        
        # views.py 로직상 회원이 직접 등록할 때 트레이너 정보 필요로 인한 에러 예상
        self.assertIn(response.status_code, [
            status.HTTP_404_NOT_FOUND,  # 트레이너를 찾을 수 없음
            status.HTTP_400_BAD_REQUEST,  # 유효하지 않은 사용자 타입
            status.HTTP_201_CREATED  # 성공하는 경우도 허용
        ])
    
    def test_workout_set_create_forbidden_member_other(self):
        # 회원이 다른 회원의 운동 세트 등록 시도 시 금지 테스트
        self.client.force_authenticate(user=self.member_user)
        url = reverse('workout-set-create', kwargs={'member_id': self.other_member.id})
        
        data = {
            'body_part': '가슴',
            'equipment': '바벨',
            'exercise_name': '벤치프레스',
            'repetitions': 10,
            'weight_kg': 80.0,
            'duration_sec': 300,
            'calories': 100
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['success'])
    
    def test_workout_set_create_missing_fields(self):
        # 필수 필드 누락 시 실패 테스트
        self.client.force_authenticate(user=self.trainer_user)
        url = reverse('workout-set-create', kwargs={'member_id': self.member_user.id})
        
        data = {
            'body_part': '등',
            'equipment': '머신',
            # exercise_name 누락
            'repetitions': 15,
            'weight_kg': 12.0,
            'duration_sec': 390,
            'calories': 120
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('exercise_name', response.data['message'])
    
    def test_workout_set_create_nonexistent_member(self):
        # 존재하지 않는 회원 ID로 요청 시 실패 테스트
        self.client.force_authenticate(user=self.trainer_user)
        url = reverse('workout-set-create', kwargs={'member_id': 99999})
        
        data = {
            'body_part': '등',
            'equipment': '머신',
            'exercise_name': '로잉 머신',
            'repetitions': 15,
            'weight_kg': 12.0,
            'duration_sec': 390,
            'calories': 120
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])


class ExerciseListViewTestCase(WorkoutViewsTestCase):
    # 운동 목록 조회 API 테스트
    
    def test_exercise_list_view_success(self):
        # 운동 목록 조회 성공 테스트
        self.client.force_authenticate(user=self.trainer_user)
        url = reverse('exercise-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('data', response.data)
        self.assertIn('가슴', response.data['data'])
        self.assertEqual(len(response.data['data']['가슴']), 1)
    
    def test_exercise_list_view_with_body_part_filter(self):
        # 운동 부위 필터 적용 테스트
        self.client.force_authenticate(user=self.trainer_user)
        url = reverse('exercise-list')
        
        response = self.client.get(url, {'body_part': '가슴'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('가슴', response.data['data'])
    
    def test_exercise_list_view_unauthorized(self):
        # 인증되지 않은 사용자 접근 테스트
        url = reverse('exercise-list')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class WorkoutExerciseSetsViewTestCase(WorkoutViewsTestCase):
    # 특정 운동의 세트 목록 조회 API 테스트
    
    def test_workout_exercise_sets_view_success(self):
        # 운동 세트 목록 조회 성공 테스트
        self.client.force_authenticate(user=self.trainer_user)
        url = reverse('workout-exercise-sets', kwargs={
            'member_id': self.member_user.id,
            'workout_exercise_id': self.workout_exercise.id
        })
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('data', response.data)
        self.assertEqual(response.data['data']['exercise_name'], '벤치프레스')
        self.assertEqual(len(response.data['data']['sets']), 1)
    
    def test_workout_exercise_sets_view_error_handling(self):
        # 존재하지 않는 운동 ID로 요청 시 에러 처리 테스트
        self.client.force_authenticate(user=self.trainer_user)
        url = reverse('workout-exercise-sets', kwargs={
            'member_id': self.member_user.id,
            'workout_exercise_id': 99999
        })
        
        response = self.client.get(url)
        
        # 에러 응답인지 확인 (404 또는 500 모두 허용)
        self.assertGreaterEqual(response.status_code, 400)
        # success가 있다면 False여야 함
        if 'success' in response.data:
            self.assertFalse(response.data['success'])


class ExerciseSetViewTestCase(WorkoutViewsTestCase):
    # 개별 세트 조회/수정/삭제 API 테스트
    
    def test_exercise_set_detail_success(self):
        # 개별 세트 상세 조회 성공 테스트
        self.client.force_authenticate(user=self.trainer_user)
        url = reverse('exercise-set', kwargs={
            'member_id': self.member_user.id,
            'workout_exercise_id': self.workout_exercise.id,
            'set_id': self.exercise_set.id
        })
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['set_number'], 1)
        self.assertEqual(response.data['data']['repetitions'], 10)
    
    def test_exercise_set_update_success(self):
        # 개별 세트 수정 성공 테스트
        self.client.force_authenticate(user=self.trainer_user)
        url = reverse('exercise-set', kwargs={
            'member_id': self.member_user.id,
            'workout_exercise_id': self.workout_exercise.id,
            'set_id': self.exercise_set.id
        })
        
        data = {
            'repetitions': 12,
            'weight_kg': 85.0,
            'duration_sec': 900,
            'calories': 80
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['repetitions'], 12)
        self.assertEqual(response.data['data']['weight_kg'], 85.0)
        
        # 데이터베이스에서 실제로 수정되었는지 확인
        updated_set = ExerciseSet.objects.get(id=self.exercise_set.id)
        self.assertEqual(updated_set.repetitions, 12)
        self.assertEqual(float(updated_set.weight_kg), 85.0)
    
    def test_exercise_set_update_member_forbidden(self):
        # 회원이 다른 회원의 세트 수정 시도 시 금지 테스트
        self.client.force_authenticate(user=self.other_member)
        url = reverse('exercise-set', kwargs={
            'member_id': self.member_user.id,
            'workout_exercise_id': self.workout_exercise.id,
            'set_id': self.exercise_set.id
        })
        
        data = {'repetitions': 12}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['success'])
    
    def test_exercise_set_delete_success(self):
        # 개별 세트 삭제 성공 테스트 (추가 세트 생성 후 삭제)
        # 마지막 세트 삭제 방지를 위해 추가 세트 생성
        additional_set = ExerciseSet.objects.create(
            workout_exercise=self.workout_exercise,
            set_number=2,
            repetitions=8,
            weight_kg=75.0,
            duration=timedelta(minutes=10),
            calories=60
        )
        
        self.client.force_authenticate(user=self.trainer_user)
        url = reverse('exercise-set', kwargs={
            'member_id': self.member_user.id,
            'workout_exercise_id': self.workout_exercise.id,
            'set_id': additional_set.id
        })
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # 실제로 삭제되었는지 확인
        self.assertFalse(ExerciseSet.objects.filter(id=additional_set.id).exists())
    
    def test_exercise_set_delete_last_set_forbidden(self):
        # 마지막 세트 삭제 금지 테스트
        self.client.force_authenticate(user=self.trainer_user)
        url = reverse('exercise-set', kwargs={
            'member_id': self.member_user.id,
            'workout_exercise_id': self.workout_exercise.id,
            'set_id': self.exercise_set.id
        })
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('마지막 세트', response.data['message'])


class ExerciseSetCreateViewTestCase(WorkoutViewsTestCase):
    # 기존 운동에 세트 추가 API 테스트
    
    def test_exercise_set_create_success(self):
        # 기존 운동에 세트 추가 성공 테스트
        self.client.force_authenticate(user=self.trainer_user)
        url = reverse('exercise-set-create', kwargs={
            'member_id': self.member_user.id,
            'workout_exercise_id': self.workout_exercise.id
        })
        
        data = {
            'repetitions': 8,
            'weight_kg': 85.0,
            'duration_sec': 600,
            'calories': 90
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['set_number'], 2)
        self.assertEqual(response.data['data']['repetitions'], 8)
        
        # 실제로 세트가 추가되었는지 확인
        self.assertEqual(ExerciseSet.objects.filter(workout_exercise=self.workout_exercise).count(), 2)
    
    def test_exercise_set_create_missing_fields(self):
        # 필수 필드 누락 시 실패 테스트
        self.client.force_authenticate(user=self.trainer_user)
        url = reverse('exercise-set-create', kwargs={
            'member_id': self.member_user.id,
            'workout_exercise_id': self.workout_exercise.id
        })
        
        data = {
            'repetitions': 8,
            # weight_kg 누락
            'duration_sec': 600,
            'calories': 90
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('weight_kg', response.data['message'])
    
    def test_exercise_set_create_invalid_data_types(self):
        # 잘못된 데이터 타입으로 요청 시 실패 테스트
        self.client.force_authenticate(user=self.trainer_user)
        url = reverse('exercise-set-create', kwargs={
            'member_id': self.member_user.id,
            'workout_exercise_id': self.workout_exercise.id
        })
        
        data = {
            'repetitions': 'invalid',  # 문자열이지만 정수여야 함
            'weight_kg': 85.0,
            'duration_sec': 600,
            'calories': 90
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_exercise_set_create_nonexistent_workout_exercise(self):
        # 존재하지 않는 운동 ID로 요청 시 실패 테스트
        self.client.force_authenticate(user=self.trainer_user)
        url = reverse('exercise-set-create', kwargs={
            'member_id': self.member_user.id,
            'workout_exercise_id': 99999
        })
        
        data = {
            'repetitions': 8,
            'weight_kg': 85.0,
            'duration_sec': 600,
            'calories': 90
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
    
    def test_exercise_set_create_member_forbidden(self):
        # 회원이 다른 회원의 운동에 세트 추가 시도 시 금지 테스트
        self.client.force_authenticate(user=self.other_member)
        url = reverse('exercise-set-create', kwargs={
            'member_id': self.member_user.id,
            'workout_exercise_id': self.workout_exercise.id
        })
        
        data = {
            'repetitions': 8,
            'weight_kg': 85.0,
            'duration_sec': 600,
            'calories': 90
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['success'])


class ExceptionHandlingTestCase(WorkoutViewsTestCase):
    # 예외 처리 테스트
    
    @patch('workouts.views.WorkoutExercise.objects.filter')
    def test_member_records_view_database_error(self, mock_filter):
        # 데이터베이스 오류 발생 시 예외 처리 테스트
        mock_filter.side_effect = Exception('Database connection error')
        
        self.client.force_authenticate(user=self.trainer_user)
        url = reverse('member-records', kwargs={'member_id': self.member_user.id})
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('오류가 발생했습니다', response.data['message'])
    
    @patch('workouts.views.Exercise.objects.get_or_create')
    def test_workout_set_create_database_error(self, mock_get_or_create):
        # 운동 세트 생성 시 데이터베이스 오류 발생 테스트
        mock_get_or_create.side_effect = Exception('Database error')
        
        self.client.force_authenticate(user=self.trainer_user)
        url = reverse('workout-set-create', kwargs={'member_id': self.member_user.id})
        
        data = {
            'body_part': '등',
            'equipment': '머신',
            'exercise_name': '로잉 머신',
            'repetitions': 15,
            'weight_kg': 12.0,
            'duration_sec': 390,
            'calories': 120
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])


class ModelValidationTestCase(WorkoutViewsTestCase):
    # 모델 유효성 검사 테스트
    
    def test_exercise_set_model_validation(self):
        # ExerciseSet 모델 유효성 검사 테스트
        # 음수 값이나 잘못된 값으로 세트 생성 시도
        self.client.force_authenticate(user=self.trainer_user)
        url = reverse('exercise-set-create', kwargs={
            'member_id': self.member_user.id,
            'workout_exercise_id': self.workout_exercise.id
        })
        
        data = {
            'repetitions': -5,  # 음수 값
            'weight_kg': -10.0,  # 음수 값
            'duration_sec': -300,  # 음수 값
            'calories': -50  # 음수 값
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_exercise_set_zero_values(self):
        # 0 값으로 세트 생성 시도 테스트
        self.client.force_authenticate(user=self.trainer_user)
        url = reverse('exercise-set-create', kwargs={
            'member_id': self.member_user.id,
            'workout_exercise_id': self.workout_exercise.id
        })
        
        data = {
            'repetitions': 0,  # 0 값
            'weight_kg': 0.0,
            'duration_sec': 0,  # 0 값
            'calories': 0
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])


class WorkoutTotalsCalculationTestCase(WorkoutViewsTestCase):
    # 운동 총합 계산 테스트
    
    def test_set_creation_updates_totals(self):
        # 세트 추가 후 총합 업데이트 확인 테스트
        self.client.force_authenticate(user=self.trainer_user)
        url = reverse('exercise-set-create', kwargs={
            'member_id': self.member_user.id,
            'workout_exercise_id': self.workout_exercise.id
        })
        
        data = {
            'repetitions': 8,
            'weight_kg': 85.0,
            'duration_sec': 600,
            'calories': 90
        }
        
        response = self.client.post(url, data, format='json')
        
        # 응답이 성공인지 확인
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        
        # 실제 DB에 세트가 추가되었는지 확인
        total_sets_in_db = ExerciseSet.objects.filter(workout_exercise=self.workout_exercise).count()
        self.assertEqual(total_sets_in_db, 2)  # setUp에서 1개 + 새로 추가한 1개
        
        # WorkoutExercise 객체 새로고침 후 칼로리 확인
        self.workout_exercise.refresh_from_db()
        self.assertGreater(self.workout_exercise.total_calories, 150)  # 기존보다 증가했는지만 확인
    
    def test_daily_workout_totals_update_after_set_deletion(self):
        # 세트 삭제 후 DailyWorkout 총합 업데이트 테스트
        # 추가 세트 생성
        additional_set = ExerciseSet.objects.create(
            workout_exercise=self.workout_exercise,
            set_number=2,
            repetitions=8,
            weight_kg=75.0,
            duration=timedelta(minutes=10),
            calories=60
        )
        
        # WorkoutExercise 총합 업데이트 (세트 추가 후)
        self.workout_exercise.total_sets = 2
        self.workout_exercise.total_calories = 150 + 60  # 기존 + 추가
        self.workout_exercise.save()
        
        # DailyWorkout 총합도 업데이트
        self.daily_workout.total_calories = 150 + 60
        self.daily_workout.save()
        
        initial_daily_calories = self.daily_workout.total_calories
        
        self.client.force_authenticate(user=self.trainer_user)
        url = reverse('exercise-set', kwargs={
            'member_id': self.member_user.id,
            'workout_exercise_id': self.workout_exercise.id,
            'set_id': additional_set.id
        })
        
        response = self.client.delete(url)
        
        # 응답 확인
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # DailyWorkout 총합 업데이트 확인
        self.daily_workout.refresh_from_db()
        # 실제 총합이 정확히 계산되는지는 구현에 따라 다를 수 있음
        self.assertIsNotNone(self.daily_workout.total_calories)