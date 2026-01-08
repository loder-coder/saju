import os
from openai import OpenAI
from google import genai


# 환경변수 가이드
# LLM_PROVIDER=gemini (또는 openai)
# GEMINI_API_KEY=AIza...
# GEMINI_MODEL=gemini-1.5-flash (원하면 gemini-1.5-pro 등으로 변경 가능)

def get_ai_analysis(prompt: str) -> str:
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    try:
        if provider == "openai":
            return _call_openai(prompt)
        else:
            return _call_gemini(prompt)
    except Exception as e:
        return f"Analysis failed: {str(e)}"


def _call_openai(prompt: str):
    """
    비용: GPT-4o-mini 기준 1M 토큰당 $0.15 (약 200원)
    모델명도 환경변수로 제어 가능
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "OpenAI API Key missing."

    client = OpenAI(api_key=api_key)
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # 기본값 gpt-4o-mini

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are a helpful life consultant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )
    return response.choices[0].message.content


def _call_gemini(prompt: str):
    """
    비용: 무료 (Pay-as-you-go 설정 시 초과분 과금)
    모델: 환경변수 GEMINI_MODEL로 제어 (기본값 gemini-1.5-flash)
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Gemini API Key missing."

    # 신규 SDK (google-genai) 사용법
    client = genai.Client(api_key=api_key)

    # 환경변수 없으면 기본값(gemini-1.5-flash) 사용
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Gemini API Error: {str(e)}"