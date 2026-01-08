import os
from openai import OpenAI
from google import genai


# 환경변수 가이드
# LLM_PROVIDER=gemini (또는 openai)
# GEMINI_API_KEY=AIza...
# GEMINI_MODEL=gemini-2.0-flash

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
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "OpenAI API Key missing."

    client = OpenAI(api_key=api_key)
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

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
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Gemini API Key missing."

    client = genai.Client(api_key=api_key)

    # 기본값 gemini-2.0-flash
    target_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    try:
        response = client.models.generate_content(
            model=target_model,
            contents=prompt
        )
        return response.text
    except Exception as e:
        # 에러 발생 시 원인 바로 확인 가능
        return f"Gemini API Error: {str(e)}"