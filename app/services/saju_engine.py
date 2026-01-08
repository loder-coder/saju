# 사주 용어 영어 매핑
GAN_EN = {
    "甲": "Yang Wood", "乙": "Yin Wood", "丙": "Yang Fire", "丁": "Yin Fire",
    "戊": "Yang Earth", "己": "Yin Earth", "庚": "Yang Metal", "辛": "Yin Metal",
    "壬": "Yang Water", "癸": "Yin Water"
}

ZHI_EN = {
    "子": "Rat (Water)", "丑": "Ox (Earth)", "寅": "Tiger (Wood)", "卯": "Rabbit (Wood)",
    "辰": "Dragon (Earth)", "巳": "Snake (Fire)", "午": "Horse (Fire)", "未": "Sheep (Earth)",
    "申": "Monkey (Metal)", "酉": "Rooster (Metal)", "戌": "Dog (Earth)", "亥": "Pig (Water)"
}


def translate_pillar(gan_zhi: str) -> str:
    if len(gan_zhi) != 2:
        return gan_zhi
    gan = GAN_EN.get(gan_zhi[0], gan_zhi[0])
    zhi = ZHI_EN.get(gan_zhi[1], gan_zhi[1])
    return f"{gan} {zhi}"


def build_saju_prompt(saju_data: dict, theme: str = "general") -> str:
    # 1. 기둥 번역
    pillars = saju_data.get("saju", {}).get("pillars", {})
    year_p = translate_pillar(pillars.get("year", ""))
    month_p = translate_pillar(pillars.get("month", ""))
    day_p = translate_pillar(pillars.get("day", ""))
    time_p = translate_pillar(pillars.get("time", ""))

    # 2. 오행 분석
    elements = saju_data.get("saju", {}).get("elements", {})
    sorted_elements = sorted(elements.items(), key=lambda x: x[1], reverse=True)
    dominant = sorted_elements[0]
    lacking = [k for k, v in elements.items() if v == 0]

    # 3. 주제별 지침
    theme_instructions = {
        "general": "Focus on general personality strengths and life advice.",
        "love": "Focus on romantic style, ideal partner, and attraction advice.",
        "career": "Focus on work style, suitable fields, and professional growth.",
        "wealth": "Focus on financial potential, investment style, and money management."
    }
    selected_instruction = theme_instructions.get(theme, theme_instructions["general"])

    # 4. 프롬프트 조립 (요약 섹션 강제)
    prompt = f"""
    You are an expert 'Life Consultant' (Saju Master). Analyze the user's Energy Blueprint.
    Theme: **{theme.upper()}**.

    [Profile]
    - Year: {year_p}, Month: {month_p}, Day: {day_p}, Time: {time_p}
    - Balance: {', '.join([f'{k}: {v}' for k, v in elements.items()])}
    - Key: Dominant {dominant[0]}, Missing {', '.join(lacking) if lacking else 'None'}

    [Task]
    {selected_instruction}

    [Output Format - STRICTLY FOLLOW THIS]
    1. Start with a section header '### SUMMARY'.
    2. Under Summary, provide exactly 3 bullet points capturing the core insight.
    3. Then, start a section header '### ANALYSIS'.
    4. Provide the detailed explanation (2-3 paragraphs).

    [Tone]
    Mystical but Modern, Insightful, Empathetic. English.
    """

    return prompt.strip()