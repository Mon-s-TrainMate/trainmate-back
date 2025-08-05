# convert_to_csv.py

import csv
import os

def convert_text_to_csv():
    # raw_data.txt 파일을 CSV로 변환
    
    # 폴더 생성
    os.makedirs('workouts/data', exist_ok=True)
    
    # 텍스트 파일 읽기
    try:
        with open('workouts/data/raw_data.txt', 'r', encoding='utf-8') as f:
            raw_data = f.read()
    except FileNotFoundError:
        print("❌ workouts/data/raw_data.txt 파일을 찾을 수 없습니다.")
        print("1. workouts/data/raw_data.txt 파일을 생성하고")
        print("2. 첨부된 전체 데이터를 복사해서 붙여넣어주세요.")
        return
    
    # CSV 파일로 저장
    lines = raw_data.strip().split('\n')
    
    with open('workouts/data/exercises.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        for line in lines:
            # 탭으로 분리
            columns = line.split('\t')
            
            # 첫 번째 컬럼(번호) 제거하고 나머지만 사용
            if len(columns) > 1:
                row = columns[1:]  # 번호 제거
                writer.writerow(row)
    
    print("✅ CSV 파일 생성 완료: workouts/data/exercises.csv")
    print(f"📊 총 {len(lines)-1}개 운동 데이터 변환")

if __name__ == "__main__":
    convert_text_to_csv()