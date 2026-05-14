import os
import json
import gc
import torch
from faster_whisper import WhisperModel

WORKSPACE = r"C:\Users\MBC\Documents\testwhisper\workspace"

def main():
    metadata_path = os.path.join(WORKSPACE, "split_metadata.json")
    if not os.path.exists(metadata_path):
        print("[오류] split_metadata.json 파일이 없습니다. 1_split.py를 먼저 실행해주세요.")
        return

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    print("Faster-Whisper 모델(large-v3)을 로드합니다...")
    # VRAM 효율을 위해 float16 설정
    model = WhisperModel("large-v3", device="cuda", compute_type="float16")

    for part_name in sorted(metadata.keys()):
        audio_path = os.path.join(WORKSPACE, part_name)
        output_json_path = os.path.join(WORKSPACE, part_name.replace(".m4a", "_unaligned.json"))

        if not os.path.exists(audio_path):
            print(f"[경고] {audio_path} 파일이 존재하지 않아 건너뜁니다.")
            continue
            
        print(f"\n[{part_name}] STT 추출을 시작합니다...")
        
        segments_generator, info = model.transcribe(
            audio_path, language="en", condition_on_previous_text=False
        )
        
        # 결과를 WhisperX에서 읽기 쉬운 형태(dict 리스트)로 변환
        unaligned_segments = []
        for segment in segments_generator:
            unaligned_segments.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            })
            print(f"진행: {segment.end:.1f}초 완료", end="\r")

        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(unaligned_segments, f, indent=4, ensure_ascii=False)
            
        print(f"\n[{part_name}] 추출 완료: {output_json_path}")

    # 작업 완료 후 VRAM 해제
    del model
    torch.cuda.empty_cache()
    gc.collect()
    print("\n[작업 완료] 모든 분할 파일의 STT 추출이 완료되었습니다.")

if __name__ == "__main__":
    main()