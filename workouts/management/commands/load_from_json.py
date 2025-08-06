import json
from django.core.management.base import BaseCommand
from workouts.models import Exercise

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
                if item.get('exercise_name') == '일치하는 운동이 없습니다.':
                    skipped_count += 1
                    continue
                
                exercise, created = Exercise.objects.get_or_create(
                    exercise_name=item['exercise_name'],
                    defaults={
                        'body_part': self._map_body_part(item.get('body_part', '가슴')),
                        'equipment': item.get('equipment', '맨몸'),
                        'measurement_unit': item.get('measurement_unit', '회'),
                        'weight_unit': item.get('weight_unit', 'none'),
                        'met_value': 3.5,
                        'is_active': True,
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f"✅ 생성: {exercise.exercise_name}")
                else:
                    skipped_count += 1
                    self.stdout.write(f"⚠️  이미 존재: {exercise.exercise_name}")
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"❌ 오류: {item.get('exercise_name', '알 수 없음')} - {e}")
                )
        
        total_processed = created_count + skipped_count + error_count
        self.stdout.write(
            self.style.SUCCESS(
                f"\n=== 로드 완료 ===\n"
                f"JSON에서 읽은 총 항목: {len(exercises_data)}개\n"
                f"✅ 생성: {created_count}개\n"
                f"⚠️  스킵: {skipped_count}개\n"
                f"❌ 에러: {error_count}개\n"
                f"처리된 총합: {total_processed}개"
            )
        )
    
    def _map_body_part(self, json_body_part):
        body_part_mapping = {
            '가슴': '가슴',
            '등': '등',
            '어깨': '어깨',
            '팔': '이두',
            '다리': '대퇴사두',
            '복부': '복근',
            '종아리': '종아리',
            '전신': '가슴',
            '승모': '승모',
            '삼두': '삼두',
            '대퇴사두': '대퇴사두',
            '햄스트링': '햄스트링',
            '둔근': '둔근',
            '전완': '전완',
        }
        return body_part_mapping.get(json_body_part, '가슴')