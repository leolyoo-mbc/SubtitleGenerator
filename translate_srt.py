import ollama

# 1. 파일 경로 설정
input_file = "C:/Users/MBC/Documents/testwhisper/final_subtitle.srt"
output_file = "C:/Users/MBC/Documents/testwhisper/korean_subtitle_sync.srt"

MODEL_NAME = "gemma2:9b"
TEMPERATURE = 0.3
CONTEXT_WINDOW = 3  # 앞뒤 맥락을 참고할 블록 수


# 2. 단일 블록 번역 함수 (앞뒤 맥락을 참고용으로만 사용)
def translate_single_block(target_block, context_before, context_after):
    prompt = """You are an expert English-to-Korean subtitle translator.
Your task is to translate ONLY the [TARGET TEXT] into natural Korean.
Use the [PREVIOUS CONTEXT] and [NEXT CONTEXT] only to understand the situation and tone.

RULES:
1. Translate ONLY the text inside the [TARGET TEXT]. Do NOT translate the context.
2. NO EXTRA TEXT: Output ONLY the translated text. No markdown, no notes, no timestamps.
"""
    # 앞쪽 맥락이 있을 경우 추가
    if context_before:
        prompt += f"\n[PREVIOUS CONTEXT (DO NOT TRANSLATE)]\n{context_before}\n"

    # 뒤쪽 맥락이 있을 경우 추가
    if context_after:
        prompt += f"\n[NEXT CONTEXT (DO NOT TRANSLATE)]\n{context_after}\n"

    # 번역할 실제 타겟 텍스트
    prompt += f"\n[TARGET TEXT TO TRANSLATE]\n{target_block}\n\nOUTPUT THE TRANSLATED TEXT ONLY:\n"

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": TEMPERATURE},
        )

        return response["message"]["content"].strip()
    except Exception as e:
        print(f"Error: {e}")
        return target_block  # 번역 실패 시 원본 텍스트 반환


# 3. 자막 읽기 및 파싱 (메타데이터 분리)
with open(input_file, "r", encoding="utf-8") as f:
    content = f.read().strip()

raw_blocks = content.split("\n\n")
parsed_blocks = []

for block in raw_blocks:
    lines = block.split("\n")
    if len(lines) >= 3:
        # SRT 표준 구조: 1번째 줄(인덱스), 2번째 줄(타임스탬프), 3번째 줄 이후(텍스트)
        index = lines[0]
        timestamp = lines[1]
        text = "\n".join(lines[2:])  # 대사가 두 줄 이상일 수 있으므로 다시 합침
        parsed_blocks.append({"index": index, "timestamp": timestamp, "text": text})

print(
    f"총 {len(parsed_blocks)}개의 자막에 대해 '메타데이터 분리 및 맥락 참고 번역'을 시작합니다..."
)

# 4. 자막을 하나씩(1 by 1) 순회하며 번역 실행
with open(output_file, "w", encoding="utf-8") as f:
    for i in range(len(parsed_blocks)):
        current_block = parsed_blocks[i]
        target_text = current_block["text"]

        # 앞쪽 맥락 텍스트만 추출 (0보다 작아지지 않도록 처리)
        start_idx = max(0, i - CONTEXT_WINDOW)
        context_before = "\n".join([b["text"] for b in parsed_blocks[start_idx:i]])

        # 뒤쪽 맥락 텍스트만 추출 (전체 길이를 넘지 않도록 처리)
        end_idx = min(len(parsed_blocks), i + 1 + CONTEXT_WINDOW)
        context_after = "\n".join([b["text"] for b in parsed_blocks[i + 1 : end_idx]])

        print(f"진행 중: {i+1} / {len(parsed_blocks)} 번 자막 번역 중...")

        # 번역 요청 (메타데이터가 제거된 순수 텍스트만 전달)
        translated_text = translate_single_block(
            target_text, context_before, context_after
        )

        # 마크다운 찌꺼기 제거 안전장치
        translated_text = (
            translated_text.replace("```srt", "").replace("```", "").strip()
        )

        # 메타데이터와 번역된 텍스트 안전하게 재결합
        final_block = f"{current_block['index']}\n{current_block['timestamp']}\n{translated_text}\n\n"

        f.write(final_block)
        f.flush()

print("🎉 싱크와 문맥이 모두 완벽한 자막 번역이 완료되었습니다!")
