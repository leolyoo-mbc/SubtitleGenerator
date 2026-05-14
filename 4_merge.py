import os
import json

WORKSPACE = r"C:\Users\MBC\Documents\testwhisper\workspace"
OVERLAP = 10.0

def format_time(seconds):
    """초 단위를 SRT 시간 형식으로 변환합니다."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def main():
    metadata_path = os.path.join(WORKSPACE, "split_metadata.json")
    if not os.path.exists(metadata_path):
        print("[오류] 메타데이터가 존재하지 않습니다.")
        return

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    all_parts = sorted(metadata.keys())
    global_words = []
    
    print("중첩 구간 분석 및 절대 시간 타임라인 정렬 중...")
    
    # 1. 단어 단위 전역 타임라인 배치
    for i, part_name in enumerate(all_parts):
        aligned_json = os.path.join(WORKSPACE, part_name.replace(".m4a", "_aligned.json"))
        if not os.path.exists(aligned_json):
            continue
            
        offset = metadata[part_name]["start_offset"]
        with open(aligned_json, "r", encoding="utf-8") as f:
            segments = json.load(f)
            
        part_words = []
        for seg in segments:
            if "words" in seg:
                for w in seg["words"]:
                    if "start" in w and "end" in w:
                        w_copy = w.copy()
                        w_copy["abs_start"] = w["start"] + offset
                        w_copy["abs_end"] = w["end"] + offset
                        w_copy["part_idx"] = i
                        part_words.append(w_copy)
                        
        # 2. 중첩 구간 단어 필터링 (T_mid 알고리즘)
        filtered_words = []
        for w in part_words:
            word_mid = (w["abs_start"] + w["abs_end"]) / 2
            keep = True
            
            # 이전 파트와의 중첩 구간 (이전 파트의 시작 시점 기준 T_mid)
            if i > 0:
                t_mid = offset + (OVERLAP / 2.0)
                if word_mid <= t_mid:
                    keep = False # 현재 파트(Part B)에서는 T_mid 이전 단어 삭제
                    
            # 다음 파트와의 중첩 구간
            if i < len(all_parts) - 1:
                next_offset = metadata[all_parts[i+1]]["start_offset"]
                t_mid = next_offset + (OVERLAP / 2.0)
                if word_mid > t_mid:
                    keep = False # 현재 파트(Part A)에서는 T_mid 이후 단어 삭제
                    
            if keep:
                filtered_words.append(w)
                
        global_words.extend(filtered_words)

    # 3. 단어를 문장으로 재구성 (일정 시간 차이나 구두점을 기준으로 문장 분할)
    print("문장 재구성 및 SRT 생성 중...")
    final_segments = []
    current_segment = []
    
    for i, w in enumerate(global_words):
        current_segment.append(w)
        
        # 문장 분리 조건: 마지막 단어에 구두점이 있거나 다음 단어와의 시간 차이가 큰 경우
        split_condition = False
        if "word" in w and any(punct in w["word"] for punct in [".", "?", "!"]):
            split_condition = True
        elif i < len(global_words) - 1 and (global_words[i+1]["abs_start"] - w["abs_end"] > 1.5):
            split_condition = True
            
        if split_condition or i == len(global_words) - 1:
            if current_segment:
                start_time = current_segment[0]["abs_start"]
                end_time = current_segment[-1]["abs_end"]
                text = " ".join([cw["word"] for cw in current_segment])
                final_segments.append({"start": start_time, "end": end_time, "text": text})
            current_segment = []

    # 4. 최종 SRT 작성
    final_srt_path = os.path.join(WORKSPACE, "final_subtitle.srt")
    with open(final_srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(final_segments, start=1):
            f.write(f"{i}\n")
            f.write(f"{format_time(seg['start'])} --> {format_time(seg['end'])}\n")
            f.write(f"{seg['text'].strip()}\n\n")

    print(f"\n[작업 완료] 자막 병합 성공! 총 문장 개수: {len(final_segments)}개")
    print(f"최종 자막 파일 경로: {final_srt_path}")

if __name__ == "__main__":
    main()