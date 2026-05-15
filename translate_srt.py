import ollama

# 1. 파일 경로 설정
input_file = "C:/Users/MBC/Documents/testwhisper/final_subtitle.srt"
output_file = "C:/Users/MBC/Documents/testwhisper/korean_subtitle_sync.srt"

MODEL_NAME = "gemma2:9b"

# 2. 단일 블록 번역 함수 (앞뒤 맥락을 참고용으로만 사용)
def translate_single_block(target_block, context_before, context_after):
    prompt = """You are an expert English-to-Korean subtitle translator.
Your task is to translate ONLY the [TARGET BLOCK] into natural Korean.
Use the [PREVIOUS CONTEXT] and [NEXT CONTEXT] only to understand the situation and tone.

RULES:
1. Translate ONLY the text inside the [TARGET BLOCK]. Do NOT translate the context.
2. PRESERVE FORMAT: Keep the exact SRT index number and timestamp from the [TARGET BLOCK].
3. NO EXTRA TEXT: Output ONLY the translated SRT block. No markdown, no notes.
"""
    # 앞쪽 맥락이 있을 경우 추가
    if context_before:
        prompt += f"\n[PREVIOUS CONTEXT (DO NOT TRANSLATE)]\n{context_before}\n"
    
    # 뒤쪽 맥락이 있을 경우 추가
    if context_after:
        prompt += f"\n[NEXT CONTEXT (DO NOT TRANSLATE)]\n{context_after}\n"

    # 번역할 실제 타겟 자막
    prompt += f"\n[TARGET BLOCK TO TRANSLATE]\n{target_block}\n\nOUTPUT THE TRANSLATED SRT ONLY:\n"
    
    try:
        response = ollama.chat(model=MODEL_NAME, messages=[
            {'role': 'user', 'content': prompt}
        ], options={'temperature': 0.0})
        
        return response['message']['content'].strip()
    except Exception as e:
        print(f"Error: {e}")
        return target_block

# 3. 자막 읽기
with open(input_file, "r", encoding="utf-8") as f:
    content = f.read().strip()

blocks = content.split('\n\n')

# 참고할 앞뒤 자막의 개수 (너무 많으면 AI가 헷갈리므로 앞뒤 2~3개가 적당합니다)
context_window = 1 

print(f"총 {len(blocks)}개의 자막에 대해 '1대1 완벽 싱크 번역(앞뒤 맥락 참고)'을 시작합니다...")

# 4. 자막을 하나씩(1 by 1) 순회하며 번역 실행
with open(output_file, "w", encoding="utf-8") as f:
    for i in range(len(blocks)):
        target_block = blocks[i]
        
        # 앞쪽 맥락 추출 (0보다 작아지지 않도록 처리)
        start_idx = max(0, i - context_window)
        context_before = '\n\n'.join(blocks[start_idx:i])
        
        # 뒤쪽 맥락 추출 (전체 길이를 넘지 않도록 처리)
        end_idx = min(len(blocks), i + 1 + context_window)
        context_after = '\n\n'.join(blocks[i+1:end_idx])
        
        print(f"진행 중: {i+1} / {len(blocks)} 번 자막 번역 중...")
        
        # 번역 요청
        translated_block = translate_single_block(target_block, context_before, context_after)
        
        # 마크다운 찌꺼기 제거 안전장치
        translated_block = translated_block.replace("```srt", "").replace("```", "").strip()
        
        f.write(translated_block + '\n\n')
        f.flush()

print("🎉 싱크와 문맥이 모두 완벽한 자막 번역이 완료되었습니다!")
