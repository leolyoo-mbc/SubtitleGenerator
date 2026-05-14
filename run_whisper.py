from faster_whisper import WhisperModel
import math

def format_timestamp(seconds: float):
    hours = math.floor(seconds / 3600)
    seconds %= 3600
    minutes = math.floor(seconds / 60)
    seconds %= 60
    milliseconds = round((seconds - math.floor(seconds)) * 1000)
    seconds = math.floor(seconds)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

# 1. 모델 설정 (GPU VRAM 활용)
model_size = "large-v3"
model = WhisperModel(model_size, device="cuda", compute_type="float16")

# 2. 오디오 파일 경로 지정 (본인의 파일 경로로 반드시 수정하세요)
audio_path = "C:/Users/MBC/Documents/testwhisper/part_000.m4a"

# 3. 텍스트화 실행 (무음 구간 건너뛰기 적용)
segments, info = model.transcribe(
    audio_path, 
    beam_size=5, 
    language="en",
    vad_filter=True,
    vad_parameters=dict(min_silence_duration_ms=500)
)

print(f"설정된 언어: {info.language} (확률: {info.language_probability:.2f})")

# 4. 결과물 저장 경로 지정 (본인의 파일 경로로 반드시 수정하세요)
output_path = "C:/Users/MBC/Documents/testwhisper/part_000.srt"

# 5. 파일 쓰기 작업
with open(output_path, "w", encoding="utf-8") as f:
    for i, segment in enumerate(segments, start=1):
        start_time = format_timestamp(segment.start)
        end_time = format_timestamp(segment.end)
        
        # 자막 블록 생성 (들여쓰기 없이 왼쪽 정렬)
        srt_block = f"{i}\n{start_time} --> {end_time}\n{segment.text.strip()}\n\n"
        
        print(srt_block.strip())  # 진행 상황 출력
        f.write(srt_block)        # 파일에 기록
        f.flush()                 # 안전한 저장을 위한 버퍼 비우기
