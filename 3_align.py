import os
import json
import gc
import torch
import whisperx

WORKSPACE = r"C:\Users\MBC\Documents\testwhisper\workspace"

def create_srt(segments, output_path):
    """정렬된 데이터를 검토용 SRT 파일로 저장합니다."""
    with open(output_path, "w", encoding="utf-8") as f:
        for i, segment in enumerate(segments, start=1):
            start = segment.get("start", 0)
            end = segment.get("end", start + 1)
            text = segment.get("text", "").strip()
            
            # SRT 시간 포맷 변환
            def format_time(seconds):
                h = int(seconds // 3600)
                m = int((seconds % 3600) // 60)
                s = int(seconds % 60)
                ms = int((seconds - int(seconds)) * 1000)
                return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
                
            f.write(f"{i}\n{format_time(start)} --> {format_time(end)}\n{text}\n\n")

def main():
    metadata_path = os.path.join(WORKSPACE, "split_metadata.json")
    if not os.path.exists(metadata_path):
        print("[오류] 메타데이터 파일이 없습니다.")
        return

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    print("WhisperX 정렬 모델을 로드합니다 (wav2vec2)...")
    align_model, align_metadata = whisperx.load_align_model(language_code="en", device="cuda")

    for part_name in sorted(metadata.keys()):
        audio_path = os.path.join(WORKSPACE, part_name)
        input_json_path = os.path.join(WORKSPACE, part_name.replace(".m4a", "_unaligned.json"))
        output_json_path = os.path.join(WORKSPACE, part_name.replace(".m4a", "_aligned.json"))
        output_srt_path = os.path.join(WORKSPACE, part_name.replace(".m4a", ".srt"))

        if not os.path.exists(input_json_path):
            continue

        print(f"\n[{part_name}] 강제 정렬을 시작합니다...")
        
        with open(input_json_path, "r", encoding="utf-8") as f:
            transcript = json.load(f)

        # 오디오 로드 및 정렬 (로컬 처리)
        audio = whisperx.load_audio(audio_path)
        result = whisperx.align(
            transcript, align_model, align_metadata, audio, device="cuda", return_char_alignments=False
        )

        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(result["segments"], f, indent=4, ensure_ascii=False)
            
        create_srt(result["segments"], output_srt_path)
        print(f"[{part_name}] 정렬 완료 및 개별 SRT 생성됨.")

    # VRAM 해제
    del align_model
    torch.cuda.empty_cache()
    gc.collect()
    print("\n[작업 완료] 모든 파일의 단어 정렬이 완료되었습니다. 개별 SRT 파일을 검토해주세요.")

if __name__ == "__main__":
    main()