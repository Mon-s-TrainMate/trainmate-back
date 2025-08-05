import json
from django.core.management.base import BaseCommand
from workouts.models import ExerciseCategory, Exercise

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
        
        for item in data:
            try:
                # 카테고리 찾기 또는 생성
                category, _ = ExerciseCategory.objects.get_or_create(
                    name=item['category']
                )
                
                # 운동 생성
                exercise, created = Exercise.objects.get_or_create(
                    name=item['name'],
                    defaults={
                        'equipment': item.get('equipment', '맨몸'),
                        'category': category,
                        'description': item.get('description', '')
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f"✅ 생성: {exercise.name}")
                else:
                    skipped_count += 1
                    
            except Exception as e:
                self.stdout.write(f"❌ 오류: {e}")
        
        self.stdout.write(
            f"완료! 생성: {created_count}개, 스킵: {skipped_count}개"
        )