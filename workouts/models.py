# workouts/management/commands/load_from_json.py

import json
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'JSON 파일에서 운동 데이터 로드'
    
    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help='JSON 파일 경로')
    
    def handle(self, *args, **options):
        file_path = options['file']
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"파일을 찾을 수 없습니다: {file_path}"))
            return
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"JSON 파싱 오류: {e}"))
            return
        
        created_count = 0
        skipped_count = 0
        error_count = 0
        
        try:
            exercises_data = data['exercise_categories']['exercises']
        except KeyError as e:
            self.stdout.write(self.style.ERROR(f"JSON 구조 오류: {e} 키를 찾을 수 없습니다"))
            return
        
        for item in exercises_data:
            try:
                # 리셋 후 올바른 필드명 사용
                exercise, created = Exercise.objects.get_or_create(
                    exercise_name=item['exercise_name'],  # models.py의 exercise_name 필드
                    defaults={
                        'body_part': '가슴',  # 모든 푸시업은 가슴 운동
                        'equipment': item.get('equipment', '맨몸'),
                        'measurement_unit': item.get('measurement_unit', '회'),
                        'weight_unit': item.get('weight_unit', 'none'),
                        'met_value': self._get_met_value_by_exercise_type(item),
                        'is_active': True,
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        f"✅ 생성: {exercise.exercise_name} "
                        f"(부위: {exercise.body_part}, 장비: {exercise.equipment})"
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(f"⚠️  이미 존재: {exercise.exercise_name}")
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"❌ 오류: {item.get('exercise_name', '알 수 없음')} - {e}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n=== 로드 완료 ===\n"
                f"✅ 생성: {created_count}개\n"
                f"⚠️  스킵: {skipped_count}개\n"
                f"❌ 에러: {error_count}개\n"
                f"총 처리: {len(exercises_data)}개"
            )
        )
    
    def _get_met_value_by_exercise_type(self, exercise_data):
        # 운동 유형에 따른 MET 값 계산 
        exercise_name = exercise_data.get('exercise_name', '').lower()
        
        if '중량' in exercise_name:
            return 4.5
        elif '다이아몬드' in exercise_name:
            return 4.0
        elif '디클라인' in exercise_name:
            return 4.2
        elif '인클라인' in exercise_name:
            return 3.2
        elif '니' in exercise_name or '무릎' in exercise_name:
            return 2.8
        elif '아처' in exercise_name:
            return 4.3
        elif '힌두' in exercise_name:
            return 4.1
        elif '파이크' in exercise_name:
            return 3.8
        else:
            return 3.5