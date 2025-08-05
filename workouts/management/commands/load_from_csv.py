# workouts/management/commands/load_from_csv.py
from django.core.management.base import BaseCommand
from django.db import transaction
from workouts.models import ExerciseCategory, Exercise
from decimal import Decimal
import csv
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'CSV 파일에서 운동 데이터를 로드합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='workouts/data/exercises.csv',
            help='CSV 파일 경로'
        )
        parser.add_argument(
            '--update-met',
            action='store_true',
            help='기존 운동의 MET 값만 업데이트'
        )

    def handle(self, *args, **options):
        csv_file = options['file']
        update_met_only = options['update_met']
        
        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'CSV 파일을 찾을 수 없습니다: {csv_file}')
            )
            return
        
        if update_met_only:
            self.update_met_values_from_csv(csv_file)
        else:
            self.load_exercises_from_csv(csv_file)

    def load_exercises_from_csv(self, csv_file):
        # CSV 파일에서 운동 데이터 로드 (인코딩 문제 해결) 
        
        # 카테고리 먼저 로드
        self.ensure_categories()
        categories = {cat.name: cat for cat in ExerciseCategory.objects.all()}
        
        created_count = 0
        skipped_count = 0
        
        # 인코딩 자동 감지 및 처리
        encodings_to_try = ['utf-8', 'cp949', 'euc-kr', 'utf-8-sig']
        
        for encoding in encodings_to_try:
            try:
                with open(csv_file, 'r', encoding=encoding) as file:
                    # 첫 줄 테스트
                    first_line = file.readline()
                    if '운동' in first_line or '가슴' in first_line:
                        self.stdout.write(f'✅ 인코딩 감지: {encoding}')
                        break
                    file.seek(0)  # 파일 포인터 초기화
            except UnicodeDecodeError:
                continue
        else:
            self.stdout.write(
                self.style.ERROR('❌ 지원하는 인코딩을 찾을 수 없습니다.')
            )
            return
        
        # 실제 데이터 로드
        with open(csv_file, 'r', encoding=encoding) as file:
            reader = csv.DictReader(file)
            
            batch = []
            batch_size = 50
            
            for row in reader:
                # 불필요한 데이터 필터링
                if (row.get('운동명', '') == '일치하는 운동이 없습니다.' or 
                    row.get('운동 부위', '') not in categories):
                    skipped_count += 1
                    continue
                
                # MET 값 계산
                exercise_name = row.get('운동명', '')
                equipment = row.get('도구', '')
                body_part = row.get('운동 부위', '')
                
                met_value = self.calculate_met_value(exercise_name, equipment, body_part)
                
                batch.append({
                    'category': categories[body_part],
                    'name': exercise_name,
                    'equipment': equipment,
                    'met_value': Decimal(str(met_value))
                })
                
                # 배치 처리
                if len(batch) >= batch_size:
                    created_count += self.process_batch(batch)
                    batch = []
            
            # 마지막 배치 처리
            if batch:
                created_count += self.process_batch(batch)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'완료! 생성: {created_count}개, 스킵: {skipped_count}개'
            )
        )

    def process_batch(self, batch):
        # 배치 단위로 운동 생성 
        created_count = 0
        
        with transaction.atomic():
            for data in batch:
                _, created = Exercise.objects.get_or_create(
                    category=data['category'],
                    name=data['name'],
                    defaults={
                        'equipment': data['equipment'],
                        'met_value': data['met_value']
                    }
                )
                if created:
                    created_count += 1
        
        return created_count

    def calculate_met_value(self, exercise_name, equipment, body_part):
        # 운동별 정확한 MET 값 계산 
        
        # 2024 Compendium 기반 정확한 값들
        exact_met_values = {
            # Calisthenics - 정확한 측정값 7.5
            '푸시 업': 7.5,
            '다이아몬드 푸시 업': 7.5,
            '와이드 푸시 업': 7.5,
            '인클라인 푸시 업': 7.5,
            '디클라인 푸시 업': 7.5,
            '풀 업': 7.5,
            '친 업': 7.5,
            '딥스': 7.5,
            '크런치': 7.5,
            '윗몸 일으키기': 7.5,
            
            # Weight training vigorous - 정확한 측정값 6.0
            '바벨 벤치 프레스': 6.0,
            '바벨 스쿼트': 6.0,
            '데드리프트': 6.0,
            '바벨 로우': 6.0,
            '오버헤드 프레스': 6.0,
            '밀리터리 프레스': 6.0,
            
            # Weight training light-moderate - 정확한 측정값 3.5
            '바이셉 컬': 3.5,
            '트라이셉 익스텐션': 3.5,
            '래터럴 레이즈': 3.5,
            '프론트 레이즈': 3.5,
            '리어 델트 레이즈': 3.5,
            
            # Stretching - 정확한 측정값 2.8
            '스트레칭': 2.8,
            '폼룰러': 2.8,
            
            # High intensity cardio - 정확한 측정값 8.0-12.0
            '버피': 8.0,
            '점프 스쿼트': 8.0,
            '마운틴 클라이머': 8.0,
            '배틀 로프': 8.5,
            '스프린트': 12.0,
            
            # Moderate cardio - 정확한 측정값 6.0-8.0
            '러닝': 8.0,
            '사이클': 7.0,
            '워킹': 4.3,
            '수영': 8.0,
        }
        
        # 정확한 값이 있는 경우
        for key, met_value in exact_met_values.items():
            if key in exercise_name:
                return met_value
        
        # 패턴 기반 추정
        return self.estimate_met_by_pattern(exercise_name, equipment, body_part)

    def estimate_met_by_pattern(self, exercise_name, equipment, body_part):
        # 패턴 기반 MET 값 추정 
        
        # 스트레칭/폼룰러
        if any(word in exercise_name for word in ['스트레칭', '폼룰러']):
            return 2.8
        
        # 유산소
        if equipment == '유산소':
            if any(word in exercise_name for word in ['스프린트', '버피', '점프']):
                return 10.0  # High intensity
            elif any(word in exercise_name for word in ['러닝', '사이클']):
                return 8.0   # Moderate-high
            else:
                return 6.0   # Moderate
        
        # 맨몸 운동
        if equipment == '맨몸':
            if any(word in exercise_name for word in ['푸시', '풀', '딥스', '크런치']):
                return 7.5   # Calisthenics
            elif any(word in exercise_name for word in ['점프', '버피']):
                return 8.0   # High intensity
            else:
                return 4.5   # Moderate bodyweight
        
        # 바벨 운동
        if equipment == '바벨':
            if any(word in exercise_name for word in ['벤치', '스쿼트', '데드', '프레스']):
                return 6.0   # Heavy compound
            elif any(word in exercise_name for word in ['컬', '레이즈', '익스텐션']):
                return 4.0   # Isolation
            else:
                return 5.0   # Moderate barbell
        
        # 덤벨 운동
        if equipment == '덤벨':
            if any(word in exercise_name for word in ['벤치', '스쿼트', '프레스']):
                return 5.5   # Compound dumbbell
            elif any(word in exercise_name for word in ['컬', '레이즈', '익스텐션']):
                return 3.5   # Isolation
            else:
                return 4.5   # Moderate dumbbell
        
        # 머신/케이블
        if equipment in ['머신', '케이블']:
            return 4.0
        
        # 밴드
        if equipment == '밴드':
            return 3.0
        
        # 기본값
        return 5.0

    def ensure_categories(self):
        """카테고리 생성 확인"""
        categories = [
            '가슴', '등', '승모', '어깨', '삼두', '이두', 
            '전완', '복근', '둔근', '햄스트링', '대퇴사두', '종아리'
        ]
        
        for name in categories:
            ExerciseCategory.objects.get_or_create(name=name)

    def update_met_values_from_csv(self, csv_file):
        # CSV 파일 기반으로 기존 운동의 MET 값만 업데이트 
        updated_count = 0
        
        # 인코딩 감지
        encodings_to_try = ['utf-8', 'cp949', 'euc-kr', 'utf-8-sig']
        
        for encoding in encodings_to_try:
            try:
                with open(csv_file, 'r', encoding=encoding) as file:
                    first_line = file.readline()
                    if '운동' in first_line:
                        break
                    file.seek(0)
            except UnicodeDecodeError:
                continue
        
        with open(csv_file, 'r', encoding=encoding) as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                exercise_name = row.get('운동명', '')
                if exercise_name == '일치하는 운동이 없습니다.':
                    continue
                
                # 기존 운동 찾기
                try:
                    exercise = Exercise.objects.get(name=exercise_name)
                    new_met = self.calculate_met_value(
                        exercise_name, 
                        row.get('도구', ''), 
                        row.get('운동 부위', '')
                    )
                    
                    if exercise.met_value != Decimal(str(new_met)):
                        old_met = exercise.met_value
                        exercise.met_value = Decimal(str(new_met))
                        exercise.save()
                        updated_count += 1
                        self.stdout.write(
                            f'업데이트: {exercise.name} {old_met} → {new_met}'
                        )
                
                except Exercise.DoesNotExist:
                    continue
        
        self.stdout.write(
            self.style.SUCCESS(f'MET 값 {updated_count}개 업데이트 완료')
        )