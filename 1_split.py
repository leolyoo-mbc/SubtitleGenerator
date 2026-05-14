import os
import json
import subprocess

# --- 설정 (경로 및 변수) ---
INPUT_FILE = r"C:\Users\MBC\Documents\testwhisper\audio.m4a"
WORKSPACE = r"C:\Users\MBC\Documents\testwhisper\workspace"
CHUNK_DURATION = 3600  # 1시간 (초)
OVERLAP = 10           # 중첩 구간 (초)

def get_audio_duration(file_path):
    """ffprobe를 사용하여 오디오 파일의 총 길이를 초 단위로 반환합니다."""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of",
        "default=noprint_wrappers=1:nokey=1", file_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return float(result.stdout.strip())

def main():
    os.makedirs(WORKSPACE, exist_ok=True)
    
    if not os.path.exists(INPUT_FILE):
        print(f"[오류] 원본 파일을 찾을 수 없습니다: {INPUT_FILE}")
        return

    print("오디오 길이를 분석 중입니다...")
    total_duration = get_audio_duration(INPUT_FILE)
    print(f"총 길이: {total_duration:.2f}초")

    metadata = {}
    current_start = 0.0
    part_num = 1

    print("오디오 분할을 시작합니다...")
    while current_start < total_duration:
        part_name = f"part{part_num:02d}.m4a"
        output_path = os.path.join(WORKSPACE, part_name)
        
        # ffmpeg 분할 명령어 (스트림 카피)
        cmd = [
            "ffmpeg", "-y", "-i", INPUT_FILE,
            "-ss", str(current_start),
            "-t", str(CHUNK_DURATION),
            "-c", "copy", output_path
        ]
        
        # 콘솔 출력을 억제하고 실행
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        metadata[part_name] = {"start_offset": current_start}
        print(f"[완료] {part_name} 생성됨 (시작 지점: {current_start:.1f}초)")
        
        current_start += (CHUNK_DURATION - OVERLAP)
        part_num += 1

    # 메타데이터 저장
    metadata_path = os.path.join(WORKSPACE, "split_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
        
    print(f"\n[작업 완료] 총 {part_num - 1}개의 파일이 성공적으로 분할되었습니다.")
    print(f"메타데이터 저장 위치: {metadata_path}")

if __name__ == "__main__":
    main()