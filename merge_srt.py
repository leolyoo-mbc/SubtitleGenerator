import os

# 1. 자막 시간을 계산해서 더해주는 함수
def add_offset(time_str, offset_seconds):
    h, m, s_ms = time_str.split(':')
    s, ms = s_ms.split(',')
    # 기존 시간에 오프셋(예: 7200초)을 더함
    total_seconds = int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0 + offset_seconds
    
    new_h = int(total_seconds // 3600)
    total_seconds %= 3600
    new_m = int(total_seconds // 60)
    total_seconds %= 60
    new_s = int(total_seconds)
    new_ms = int(round((total_seconds - new_s) * 1000))
    return f"{new_h:02d}:{new_m:02d}:{new_s:02d},{new_ms:03d}"

# 최종 저장될 10시간짜리 자막 파일 경로
output_file = "C:/Users/MBC/Documents/testwhisper/final_subtitle.srt"
global_index = 1  # 1번부터 10000번 이상까지 순번을 새로 매길 변수

with open(output_file, "w", encoding="utf-8") as outfile:
    # 0번부터 5번 파일까지 총 6번 반복
    for file_num in range(6):  
        # 사용자님의 파일명에 맞게 경로 지정 (part_000.srt ~ part_005.srt 가정)
        # 만약 파일명이 subtitle_0.srt 형태라면 그에 맞게 수정해주세요.
        file_path = f"C:/Users/MBC/Documents/testwhisper/part_{file_num:03d}.srt" 
        
        # 각 파일마다 더해줄 시간 (0시간, 2시간, 4시간...)
        offset_seconds = file_num * 7200
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content: continue
                
                # 자막 블록 단위로 쪼개기
                blocks = content.split('\n\n')
                for block in blocks:
                    lines = block.split('\n')
                    if len(lines) >= 3:
                        times = lines[1].split(' --> ')
                        if len(times) == 2:
                            # 시간 더하기
                            new_start = add_offset(times[0], offset_seconds)
                            new_end = add_offset(times[1], offset_seconds)
                            
                            # 새 파일에 기록하기
                            outfile.write(f"{global_index}\n")
                            outfile.write(f"{new_start} --> {new_end}\n")
                            for text_line in lines[2:]:
                                outfile.write(f"{text_line}\n")
                            outfile.write("\n")
                            
                            global_index += 1
        except Exception as e:
            print(f"에러 발생 ({file_path}): {e}")

print("10시간 단일 자막 생성 완료! final_subtitle.srt 파일을 확인해주세요.")