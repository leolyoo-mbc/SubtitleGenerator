import re

# 1. 경로 설정
input_file = "C:/Users/MBC/Documents/testwhisper/final_subtitle.srt"
output_file = "C:/Users/MBC/Documents/testwhisper/merged_english_subtitle.srt"

with open(input_file, "r", encoding="utf-8") as f:
    content = f.read().strip()

blocks = content.split('\n\n')

merged_blocks = []
current_start = None
current_end = None
current_text = []

print("영어 자막 문장 단위 병합을 시작합니다...")

# 2. 자막을 순회하며 마침표 단위로 묶기
for block in blocks:
    lines = block.split('\n')
    if len(lines) < 3: continue
    
    times = lines[1].split(' --> ')
    # 텍스트 추출 (여러 줄일 경우 한 줄로 띄어쓰기하여 합침)
    text = ' '.join(lines[2:]).strip()
    
    # 첫 자막의 시작 시간을 기록
    if current_start is None:
        current_start = times[0]
        
    # 끝 시간은 계속 현재 자막의 끝 시간으로 갱신
    current_end = times[1]
    current_text.append(text)
    
    # 3. 핵심: 텍스트가 문장 종료 기호( . ? ! )로 끝나는지 확인
    if re.search(r'[.!?]$', text) or re.search(r'[.!?]"$', text):
        merged_blocks.append({
            'start': current_start,
            'end': current_end,
            'text': ' '.join(current_text)
        })
        # 다음 문장을 위해 초기화
        current_start = None
        current_end = None
        current_text = []

# 혹시 마지막 문장에 마침표가 없어서 남은 텍스트가 있다면 처리
if current_text:
    merged_blocks.append({
        'start': current_start,
        'end': current_end,
        'text': ' '.join(current_text)
    })

# 4. 병합된 새로운 SRT 파일 저장
with open(output_file, "w", encoding="utf-8") as f:
    for i, block in enumerate(merged_blocks, 1):
        f.write(f"{i}\n")
        f.write(f"{block['start']} --> {block['end']}\n")
        f.write(f"{block['text']}\n\n")

print(f"완료! 기존 {len(blocks)}개의 자막이 {len(merged_blocks)}개의 완전한 문장 자막으로 병합되었습니다.")
