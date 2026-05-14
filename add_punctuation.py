import ollama

# 1. 파일 경로 설정
input_file = "C:/Users/MBC/Documents/testwhisper/final_subtitle.srt"
output_file = "C:/Users/MBC/Documents/testwhisper/punctuated_english.srt"

MODEL_NAME = "gemma2:9b"

def restore_punctuation(target_chunk, context_before="", context_after=""):
    prompt = """You are an Expert ASR (Automatic Speech Recognition) Post-Editor.
The [TARGET SRT] contains raw, damaged speech-to-text output. Your task is to RESTORE logical sentence boundaries by fixing capitalization and punctuation.

RULES:
1. CAPITALIZE NEW SENTENCES: Capitalize the first letter ONLY when a logically new sentence begins, or for true proper nouns.
2. CONTINUATIONS REMAIN LOWERCASE (CRITICAL): If a subtitle block simply continues an ongoing sentence from the previous block (e.g., an adjective followed by a noun in the next block), DO NOT capitalize the first word of the new block.
3. ADD PUNCTUATION: Add a period (.), question mark (?), or exclamation mark (!) ONLY at the true logical end of a complete sentence.
4. REMOVE ERRORS: If a punctuation mark breaks a logically continuous sentence in the middle, remove it.
5. PRESERVE WORDS & FORMAT: DO NOT change actual spoken words. DO NOT change Index numbers or Timestamps. Keep them EXACTLY as they are.

[EXAMPLE OF CORRECTION]
Original:
50
00:02:26,860 --> 00:02:30,900
with that logic working, we will then implement a proper character visual with the included

51
00:02:30,900 --> 00:02:31,900
assets.

Corrected Output:
50
00:02:26,860 --> 00:02:30,900
With that logic working, we will then implement a proper character visual with the included

51
00:02:30,900 --> 00:02:31,900
assets.
[END OF EXAMPLE]
"""

    if context_before:
        prompt += f"\n[PREVIOUS CONTEXT]\n{context_before}\n"
    if context_after:
        prompt += f"\n[NEXT CONTEXT]\n{context_after}\n"

    prompt += f"\n[TARGET SRT TO CORRECT]\n{target_chunk}\n\n[OUTPUT THE CORRECTED SRT ONLY]\n"
    
    try:
        response = ollama.chat(model=MODEL_NAME, messages=[
            {'role': 'user', 'content': prompt}
        ], options={'temperature': 0.0})
        
        return response['message']['content'].strip()
    except Exception as e:
        print(f"Error: {e}")
        return target_chunk

# 파일 읽기
with open(input_file, "r", encoding="utf-8") as f:
    content = f.read().strip()

blocks = content.split('\n\n')
chunk_size = 5      
context_window = 2   

print(f"총 {len(blocks)}개의 자막에 대해 '문장 부호 복원(Punctuation Restoration)'을 시작합니다...")

with open(output_file, "w", encoding="utf-8") as f:
    for i in range(0, len(blocks), chunk_size):
        current_chunk_blocks = blocks[i:i + chunk_size]
        target_chunk = '\n\n'.join(current_chunk_blocks)
        
        start_idx = max(0, i - context_window)
        context_before = '\n\n'.join(blocks[start_idx:i])
        
        end_idx = min(len(blocks), i + chunk_size + context_window)
        context_after = '\n\n'.join(blocks[i + chunk_size:end_idx])
        
        print(f"진행 중: {i+1} ~ {min(i + chunk_size, len(blocks))} 번 구간 문장 부호 복원 중...")
        
        # AI에게 문장 부호만 추가하도록 요청
        punctuated_result = restore_punctuation(target_chunk, context_before, context_after)
        punctuated_result = punctuated_result.replace("```srt", "").replace("```", "").strip()
        
        f.write(punctuated_result + "\n\n")
        f.flush()

print("🎉 문장 부호 복원이 완료되었습니다! punctuated_english.srt 파일이 생성되었습니다.")
