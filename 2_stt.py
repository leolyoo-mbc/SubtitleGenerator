import os
import json
import gc
import torch
from faster_whisper import WhisperModel

WORKSPACE = r"C:\Users\MBC\Documents\testwhisper\workspace"


def main():
    metadata_path = os.path.join(WORKSPACE, "split_metadata.json")
    if not os.path.exists(metadata_path):
        print(
            "[오류] split_metadata.json 파일이 없습니다. 1_split.py를 먼저 실행해주세요."
        )
        return

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    print("Faster-Whisper 모델(large-v3)을 로드합니다...")
    model = WhisperModel("large-v3", device="cuda", compute_type="float16")

    for part_name in sorted(metadata.keys()):
        audio_path = os.path.join(WORKSPACE, part_name)
        output_json_path = os.path.join(
            WORKSPACE, part_name.replace(".m4a", "_unaligned.json")
        )
        temp_jsonl_path = output_json_path + "l"  # 임시 저장을 위한 .jsonl 확장자

        if not os.path.exists(audio_path):
            print(f"[경고] {audio_path} 파일이 존재하지 않아 건너뜁니다.")
            continue

        print(f"\n[{part_name}] STT 추출을 시작합니다...")

        # 1. 최적화된 파라미터 적용 (VAD, Beam Size, 이전 텍스트 조건 해제)
        segments_generator, info = model.transcribe(
            audio_path,
            language="en",
            condition_on_previous_text=True,  # 환각 루프 방지
            beam_size=5,  # 속도 향상 (기본값 5)
            # vad_filter=True,  # 무음 구간 스킵 (속도 대폭 향상)
            # vad_parameters=dict(min_silence_duration_ms=500),
        )

        # 2. 실시간 안전 기록 (JSONL 방식 - 에러 발생 시 데이터 보존)
        with open(temp_jsonl_path, "w", encoding="utf-8") as f_temp:
            for segment in segments_generator:
                data = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                }
                # 리스트 메모리 적재 없이 파일에 바로 한 줄씩 기록
                json.dump(data, f_temp, ensure_ascii=False)
                f_temp.write("\n")
                print(f"진행: {segment.end:.1f}초 완료", end="\r")

        # 3. 작업 완료 후 JSONL 파일을 읽어 예쁜 JSON 리스트로 덮어쓰기 포맷팅
        final_list = []
        with open(temp_jsonl_path, "r", encoding="utf-8") as f_temp:
            for line in f_temp:
                if line.strip():
                    final_list.append(json.loads(line))

        with open(output_json_path, "w", encoding="utf-8") as f_final:
            json.dump(final_list, f_final, indent=4, ensure_ascii=False)

        # 포맷팅 완료 후 임시 JSONL 파일 삭제
        os.remove(temp_jsonl_path)

        print(f"\n[{part_name}] 추출 완료: {output_json_path}")

    # 작업 완료 후 VRAM 해제
    del model
    torch.cuda.empty_cache()
    gc.collect()
    print("\n[작업 완료] 모든 분할 파일의 STT 추출이 완료되었습니다.")


if __name__ == "__main__":
    main()
