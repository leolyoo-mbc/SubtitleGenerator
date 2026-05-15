import os
import json
import gc
import re
import warnings
import torch
from transformers import pipeline

# HuggingFace의 불필요한 Sequential 경고창 숨기기
warnings.filterwarnings("ignore")

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
    
    print("1단계: 중첩 구간(T_mid) 분석 및 절대 시간 타임라인 정렬 중...")
    
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
                    if "start" in w and "end" in w and "word" in w:
                        w_copy = w.copy()
                        w_copy["abs_start"] = w["start"] + offset
                        w_copy["abs_end"] = w["end"] + offset
                        part_words.append(w_copy)
                        
        filtered_words = []
        for w in part_words:
            word_mid = (w["abs_start"] + w["abs_end"]) / 2
            keep = True
            if i > 0 and word_mid <= (offset + OVERLAP / 2.0):
                keep = False 
            if i < len(all_parts) - 1 and word_mid > (metadata[all_parts[i+1]]["start_offset"] + OVERLAP / 2.0):
                keep = False 
            if keep:
                filtered_words.append(w)
                
        global_words.extend(filtered_words)

    print("2단계: 딥러닝 문장 부호 복원 AI 모델 로드 중...")
    device_id = 0 if torch.cuda.is_available() else -1
    
    punct_pipe = pipeline(
        "token-classification", 
        model="oliverguhr/fullstop-punctuation-multilang-large", 
        device=device_id,
        aggregation_strategy="simple" 
    )
    
    label_map = {
        "LABEL_0": "", "0": "",
        "LABEL_1": ".", ".": ".",
        "LABEL_2": ",", ",": ",",
        "LABEL_3": "?", "?": "?",
        "LABEL_4": "-", "-": "-",
        "LABEL_5": ":", ":": ":"
    }
    
    print("3단계: 중앙값 거리 스냅(Midpoint Snap) 기반 정밀 맥락 분석 중...")
    CHUNK_SIZE = 250
    total_chunks = (len(global_words) // CHUNK_SIZE) + 1

    for i in range(0, len(global_words), CHUNK_SIZE):
        chunk_words = global_words[i:i+CHUNK_SIZE]
        text = ""
        word_char_spans = []
        
        for cw in chunk_words:
            clean_w = re.sub(r'[^\w\']', '', cw["word"]).strip()
            if not clean_w:
                continue
                
            start_char = len(text)
            if start_char > 0:
                text += " "
                start_char += 1
            text += clean_w
            end_char = len(text)
            
            word_char_spans.append((start_char, end_char, cw))
            
        outputs = punct_pipe(text)
        
        for out in outputs:
            raw_entity = out.get("entity", out.get("entity_group", "")).strip()
            entity = label_map.get(raw_entity, raw_entity)
            
            if entity in {'.', ',', '?', '!', '-', ':'}:
                p_start = out["start"]
                p_end = out["end"]
                # 예측된 구두점 영역의 정중앙 위치
                p_mid = (p_start + p_end) / 2.0
                
                best_w = None
                min_dist = float('inf')
                
                # 가장 거리가 가까운 단어 찾기 (오차 원천 차단)
                for start_char, end_char, cw in word_char_spans:
                    w_mid = (start_char + end_char) / 2.0
                    dist = abs(w_mid - p_mid)
                    if dist < min_dist:
                        min_dist = dist
                        best_w = cw
                        
                if best_w:
                    best_w["punct"] = entity
                    if entity in {'.', '?', '!'}:
                        best_w["is_sentence_end"] = True
                    elif entity == ',':
                        best_w["is_comma"] = True
                        
        print(f"맥락 분석 진행률: {(i // CHUNK_SIZE) + 1} / {total_chunks}", end="\r")

    print("\n4단계: 식별된 맥락 경계 기반으로 자막 완벽 재구성 중...")
    final_segments = []
    sub_segment = []
    
    SOFT_MAX_WORDS = 15
    MAX_WORDS = 30
    SILENCE_GAP = 1.5

    for i, w in enumerate(global_words):
        sub_segment.append(w)
        split_condition = False
        
        if w.get("is_sentence_end", False):
            split_condition = True
        elif len(sub_segment) >= SOFT_MAX_WORDS and w.get("is_comma", False):
            split_condition = True
        elif i < len(global_words) - 1 and (global_words[i+1]["abs_start"] - w["abs_end"] > SILENCE_GAP):
            split_condition = True
        elif len(sub_segment) >= MAX_WORDS:
            split_condition = True
            
        if split_condition or i == len(global_words) - 1:
            if sub_segment:
                start_time = sub_segment[0]["abs_start"]
                end_time = sub_segment[-1]["abs_end"]
                
                text_content = ""
                for cw in sub_segment:
                    clean_w = re.sub(r'[^\w\']', '', cw["word"]).strip()
                    if not clean_w:
                        continue
                        
                    text_content += clean_w
                    if cw.get("punct"):
                        text_content += cw["punct"]
                    text_content += " "
                    
                final_segments.append({"start": start_time, "end": end_time, "text": text_content.strip()})
            sub_segment = []

    final_srt_path = os.path.join(WORKSPACE, "final_subtitle.srt")
    with open(final_srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(final_segments, start=1):
            f.write(f"{i}\n")
            f.write(f"{format_time(seg['start'])} --> {format_time(seg['end'])}\n")
            f.write(f"{seg['text'].strip()}\n\n")

    del punct_pipe
    torch.cuda.empty_cache()
    gc.collect()

    print(f"\n[작업 완료] V5 중앙값 알고리즘 적용 완료! 총 자막 블록: {len(final_segments)}개")
    print(f"최종 자막 파일 위치: {final_srt_path}")

if __name__ == "__main__":
    main()
