# workouts/management/commands/load_from_json.py

import json
from django.core.management.base import BaseCommand
from workouts.models import Exercise

class Command(BaseCommand):
    help = 'JSON 파일에서 운동 데이터 로드'
    
    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help='JSON 파일 경로')
    
    def handle(self, *args, **options):
        file_path = options['file']
        
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        created_count = 0
        skipped_count = 0
        
        # JSON 구조에서 exercises 배열 추출
        exercises_data = data['exercise_categories']['exercises']
        
        for item in exercises_data:
            try:
                # 실제 데이터베이스 테이블 구조에 맞춰 매핑
                exercise, created = Exercise.objects.get_or_create(
                    name=item['exercise_name'],  # JSON의 exercise_name → DB의 name
                    defaults={
                        'equipment': item.get('equipment', '맨몸'),  # equipment 필드 (nullable이므로 기본값 설정)
                        'met_value': 3.0,  # 기본 MET 값 (운동 강도, NOT NULL이므로 필수)
                        'is_active': True,  # 활성 상태 (NOT NULL이므로 필수)
                        # created_at은 Django가 자동으로 현재 시간 설정
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f"✅ 생성: {exercise.name} (장비: {exercise.equipment})")
                else:
                    skipped_count += 1
                    self.stdout.write(f"⚠️  이미 존재: {exercise.name}")
                    
            except Exception as e:
                self.stdout.write(f"❌ 오류: {item.get('exercise_name', '알 수 없음')} - {e}")
        
        self.stdout.write(
            self.style.SUCCESS(f"완료! ✅ 생성: {created_count}개, ⚠️  스킵: {skipped_count}개")
        )