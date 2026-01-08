# ... (GAN_EN, ZHI_EN, translate_pillar 함수는 기존과 동일 - 생략 가능하지만 전체 코드 제공)
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
    if len(gan_zhi) != 2: return gan_zhi
    gan = GAN_EN.get(gan_zhi[0], gan_zhi[0])
    zhi = ZHI_EN.get(gan_zhi[1], gan_zhi[1])
    return f"{gan} {zhi}"


def build_saju_prompt(saju_data: dict, theme: str = "general") -> str:
    pillars = saju_data.get("saju", {}).get("pillars", {})
    year_p = translate_pillar(pillars.get("year", ""))
    month_p = translate_pillar(pillars.get("month", ""))
    day_p = translate_pillar(pillars.get("day", ""))
    time_p = translate_pillar(pillars.get("time", ""))

    elements = saju_data.get("saju", {}).get("elements", {})
    sorted_elements = sorted(elements.items(), key=lambda x: x[1], reverse=True)
    dominant = sorted_elements[0]
    lacking = [k for k, v in elements.items() if v == 0]

    theme_instructions = {
        "general": "General personality strengths and life advice.",
        "love": "Romantic style, attraction, and compatibility.",
        "career": "Work style, suitable fields, and success strategy.",
        "wealth": "Financial potential and money management."
    }
    selected_instruction = theme_instructions.get(theme, theme_instructions["general"])

    prompt = f"""
    You are an expert 'Life Consultant'. Analyze this Energy Blueprint. Theme: **{theme.upper()}**.

    [Profile]
    - Day Pillar (Self): {day_p}
    - Balance: {', '.join([f'{k}: {v}' for k, v in elements.items()])}
    - Key: Dominant {dominant[0]}, Missing {', '.join(lacking) if lacking else 'None'}

    [Task]
    {selected_instruction}

    [Output Format - STRICTLY FOLLOW]
    1. Start with '### SUMMARY'.
    2. Provide exactly 3 short bullet points. Each point must start with an **Emoji** and a **Bold Keyword**, followed by a single short sentence.
       Example:
       - 🔥 **Passionate Leader**: You naturally take charge in relationships.
       - 🌊 **Emotional Depth**: Your intuition is your superpower.
       - ⚖️ **Balance Needed**: Practice patience when stressed.
    3. Then, start '### ANALYSIS'.
    4. Provide the detailed explanation (keep it under 200 words, concise and impactful).

    [Tone]
    Modern, Trendy, Insightful. English.
    """

    return prompt.strip()