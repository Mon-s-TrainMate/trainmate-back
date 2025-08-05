# workouts/models.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal



class Exercise(models.Model):

    # 운동 부위 선택지(가슴, 등, 어깨, 이두 등)
    BODY_PART_CHOICES = [
        ('가슴', '가슴'),
        ('등', '등'),
        ('어깨', '어깨'),
        ('이두', '이두'),
        ('삼두', '삼두'),
        ('복근', '복근'),
        ('대퇴사두', '대퇴사두'),
        ('햄스트링', '햄스트링'),
        ('둔근', '둔근'),
        ('종아리', '종아리'),
        ('전완', '전완'),
        ('승모', '승모'),
    ]

    # 개별 운동 정보(벤치프레스, 랫풀다운, 스쿼트 등)
    EQUIPMENT_CHOICES = [
        ('맨몸', '맨몸'),
        ('덤벨', '덤벨'),
        ('바벨', '바벨'),
        ('머신', '머신'),
        ('케이블', '케이블'),
        ('스미스 머신', '스미스 머신'),
        ('밴드', '밴드'),
        ('스트레칭', '스트레칭'),
        ('유산소', '유산소')
    ]

    # 입력 타입 선택지 (JSON의 input_type)
    INPUT_TYPE_CHOICES = [
        ('Drop down type 01', 'Drop down type 01'),
        ('Drop down type 02', 'Drop down type 02'),
        ('Drop down type 03', 'Drop down type 03'),
        ('Drop down type 04', 'Drop down type 04'),
        ('Drop down type 05', 'Drop down type 05'),
    ]

    # 측정 단위 선택지 (JSON의 measurement_unit)
    MEASUREMENT_UNIT_CHOICES = [
        ('회', '회'),
        ('분', '분'),
        ('초', '초'),
        ('km', 'km'),
        ('m', 'm'),
        ('세트', '세트'),
    ]

    # 중량 단위 선택지 (JSON의 weight_unit)
    WEIGHT_UNIT_CHOICES = [
        ('none', '없음'),
        ('kg', 'kg'),
        ('lb', 'lb'),
    ]

    exercise_name = models.CharField(
        max_length=100,
        verbose_name="운동명"
    )

    body_part = models.CharField(
        max_length=50,
        choices=BODY_PART_CHOICES,
        verbose_name="운동 부위"
    )

    equipment = models.CharField(
        max_length=50,
        choices=EQUIPMENT_CHOICES,
        verbose_name="운동 도구"
    )

    input_type = models.CharField(
        max_length=50,
        choices=INPUT_TYPE_CHOICES,
        default='Drop down type 05',
        verbose_name="입력 타입"
    )

    measurement_unit = models.CharField(
        max_length=20,
        choices=MEASUREMENT_UNIT_CHOICES,
        default='회',
        verbose_name="측정 단위"
    )

    weight_unit = models.CharField(
        max_length=10,
        choices=WEIGHT_UNIT_CHOICES,
        default='none',
        verbose_name="중량 단위"
    )

    met_value = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=Decimal('6.0'),
        validators=[MinValueValidator(Decimal('1.0')), MaxValueValidator(Decimal('20.0'))],
        verbose_name="MET 값",
        help_text="칼로리 계산용 MET 값 (1.0-20.0)"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="활성화 여부"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성일시"
    )

    class Meta:
        verbose_name = "운동"
        verbose_name_plural = "운동들"
        ordering = ['body_part', 'exercise_name']
        indexes = [
            models.Index(fields=['body_part', 'is_active']),
            models.Index(fields=['equipment']),
        ]

    def __str__(self):
        return f"{self.body_part} - {self.exercise_name}"



class DailyWorkout(models.Model):
    # 일일 운동 세션

    member = models.ForeignKey(
        'members.Member',
        on_delete=models.CASCADE,
        related_name='daily_workouts',
        verbose_name="회원"
    )

    trainer = models.ForeignKey(
        'members.Trainer',
        on_delete=models.CASCADE,
        related_name='daily_workouts',
        verbose_name="트레이너"
    )

    workout_date = models.DateField(
        verbose_name="운동 날짜"
    )

    total_duration = models.DurationField(
        blank=True,
        null=True,
        verbose_name="총 운동시간",
        help_text="예: 00:47:01"
    )

    total_calories = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="총 소모 칼로리"
    )

    is_completed = models.BooleanField(
        default=False,
        verbose_name="운동 완료 여부"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성일시"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="수정일시"
    )

    class Meta:
        verbose_name = "일일 운동"
        verbose_name_plural = "일일 운동들"
        ordering = ['-workout_date', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['member', 'workout_date'],
                name='unique_member_workout_date'
            )
        ]
        indexes = [
            models.Index(fields=['member', 'workout_date']),
            models.Index(fields=['trainer']),
            models.Index(fields=['is_completed']),
        ]

    def __str__(self):
        return f"{self.member} - {self.workout_date}"
    
    def calculate_total_calories(self):
        # 총 칼로리 계산 메서드
        return sum(exercise.total_calories for exercise in self.workout_exercises.all())
    
    def calculate_total_duration(self):
        # 총 운동시간 계산 메서드
        from datetime import timedelta
        total = timedelta()
        for exercise in self.workout_exercises.all():
            if exercise.total_duration:
                total += exercise.total_duration
        return total



class WorkoutExercise(models.Model):
    # 운동 세션 내 개별 운동

    daily_workout = models.ForeignKey(
        DailyWorkout,
        on_delete=models.CASCADE,
        related_name='workout_exercises',
        verbose_name="일일 운동"
    )

    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name='workout_exercises',
        verbose_name="운동"
    )

    order_number = models.PositiveIntegerField(
        verbose_name="운동 순서",
        help_text="1, 2, 3... (화면에서 01, 02, 03으로 표시)"
    )

    total_sets = models.PositiveIntegerField(
        default=0,
        verbose_name="총 세트 수"
    )

    total_duration = models.DurationField(
        blank=True,
        null=True,
        verbose_name="해당 운동 총 시간"
    )

    total_calories = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="해당 운동 총 칼로리"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성일시"
    )

    class Meta:
        verbose_name = "운동 항목"
        verbose_name_plural = "운동 항목들"
        ordering = ['daily_workout', 'order_number']
        constraints = [
            models.UniqueConstraint(
                fields=['daily_workout', 'order_number'],
                name='unique_workout_order'
            )
        ]
        indexes = [
            models.Index(fields=['daily_workout', 'order_number']),
        ]

    def __str__(self):
        return f"{self.daily_workout} - {self.order_number:02d}. {self.exercise.exercise_name}"
    
    def calculate_calories(self, member_weight_kg=70):
        # 칼로리 계산 메서드 (MET 공식 사용)
        if self.total_duration:
            hours = self.total_duration.total_seconds() / 3600
            # 칼로리 = MET × 체중(kg) × 시간(h)
            calories = float(self.exercise.met_value) * member_weight_kg * hours
            return int(calories)
        return 0



class ExerciseSet(models.Model):
    # 운동 세트별 정보

    workout_exercise = models.ForeignKey(
        WorkoutExercise,
        on_delete=models.CASCADE,
        related_name='exercise_sets',
        verbose_name="운동 항목"
    )

    set_number = models.PositiveIntegerField(
        verbose_name="세트 번호"
    )

    repetitions = models.PositiveIntegerField(
        verbose_name="횟수",
        help_text="예: 15회"
    )

    weight_kg = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="중량(kg)",
        help_text="예: 24.00kg"
    )

    duration = models.DurationField(
        verbose_name="세트별 소요시간",
        help_text="예: 00:04:22"
    )

    calories = models.IntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="세트별 칼로리"
    )

    completed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="세트 완료 시간"
    )

    class Meta:
        verbose_name = "운동 세트"
        verbose_name_plural = "운동 세트들"
        ordering = ['workout_exercise', 'set_number']
        constraints = [
            models.UniqueConstraint(
                fields=['workout_exercise', 'set_number'],
                name='unique_exercise_set_number'
            )
        ]
        indexes = [
            models.Index(fields=['workout_exercise', 'set_number']),
        ]

    def __str__(self):
        return f"{self.workout_exercise} - 세트{self.set_number}"
    
    def calculate_calories(self, member_weight_kg=70):
        # 개별 세트 칼로리 계산 
        hours = self.duration.total_seconds() / 3600
        # 칼로리 = MET × 체중(kg) × 시간(h)
        calories = float(self.workout_exercise.exercise.met_value) * member_weight_kg * hours
        return int(calories)
    
    @property
    def display_weight(self):
        # 중량을 보기 좋게 표시
        if self.weight_kg == int(self.weight_kg):
            return f"{int(self.weight_kg)}kg"
        return f"{self.weight_kg}kg"