# 사주 용어 영어 매핑
GAN_EN = {
    "甲": "Yang Wood", "乙": "Yin Wood",
    "丙": "Yang Fire", "丁": "Yin Fire",
    "戊": "Yang Earth", "己": "Yin Earth",
    "庚": "Yang Metal", "辛": "Yin Metal",
    "壬": "Yang Water", "癸": "Yin Water"
}

ZHI_EN = {
    "子": "Rat (Water)", "丑": "Ox (Earth)", "寅": "Tiger (Wood)", "卯": "Rabbit (Wood)",
    "辰": "Dragon (Earth)", "巳": "Snake (Fire)", "午": "Horse (Fire)", "未": "Sheep (Earth)",
    "申": "Monkey (Metal)", "酉": "Rooster (Metal)", "戌": "Dog (Earth)", "亥": "Pig (Water)"
}


def translate_pillar(gan_zhi: str) -> str:
    """
    예: 戊寅 -> Yang Earth Tiger
    """
    if len(gan_zhi) != 2:
        return gan_zhi

    gan = GAN_EN.get(gan_zhi[0], gan_zhi[0])
    zhi = ZHI_EN.get(gan_zhi[1], gan_zhi[1])
    return f"{gan} {zhi}"


def build_saju_prompt(saju_data: dict, theme: str = "general") -> str:
    """
    주제(theme)에 따라 다른 프롬프트를 생성함
    theme: 'general', 'love', 'career', 'wealth'
    """

    # 1. 기둥 번역
    pillars = saju_data.get("saju", {}).get("pillars", {})
    year_p = translate_pillar(pillars.get("year", ""))
    month_p = translate_pillar(pillars.get("month", ""))
    day_p = translate_pillar(pillars.get("day", ""))
    time_p = translate_pillar(pillars.get("time", ""))

    # 2. 오행 분석
    elements = saju_data.get("saju", {}).get("elements", {})
    # 많은 것과 적은 것 찾기
    sorted_elements = sorted(elements.items(), key=lambda x: x[1], reverse=True)
    dominant = sorted_elements[0]  # 가장 많은 것
    lacking = [k for k, v in elements.items() if v == 0]  # 없는 것

    # 3. 주제별 지침 설정 (페르소나 변경)
    theme_instructions = {
        "general": """
            1. Define their 'Core Archetype' based on the Day Pillar.
            2. Explain their general personality strengths based on Dominant Energy.
            3. Give 1 practical piece of life advice based on Missing Energy.
        """,
        "love": """
            1. Analyze their romantic style based on the Day Pillar (Core Self) and Element Balance.
            2. Explain what kind of partner suits them best.
            3. If they lack Fire/Water, give advice on expressing emotion. If they lack Earth/Metal, give advice on stability.
            4. Focus specifically on Love, Attraction, and Relationships.
        """,
        "career": """
            1. Analyze their work style based on the Month Pillar (Career Environment) and Dominant Energy.
            2. Suggest 2-3 suitable career fields or roles (e.g., Leadership, Creative, Analytical).
            3. Give advice on how to handle workplace stress based on their Missing Energy.
            4. Focus specifically on Career, Business, and Professional Growth.
        """,
        "wealth": """
            1. Analyze their potential for wealth accumulation based on Element Balance.
            2. Is their energy better suited for steady saving (Earth) or bold investments (Fire/Metal)?
            3. Give practical financial advice based on their chart.
            4. Focus specifically on Money, Investment, and Financial Stability.
        """
    }

    # 테마가 없거나 이상하면 general로 처리
    selected_instruction = theme_instructions.get(theme, theme_instructions["general"])

    # 4. 프롬프트 조립
    prompt = f"""
    You are an expert 'Life Consultant' specializing in Eastern philosophy (Saju).
    The user has asked for a specific analysis on: **{theme.upper()}**.

    [User Profile]
    - Year Pillar (Social/Roots): {year_p}
    - Month Pillar (Career/Environment): {month_p}
    - Day Pillar (Self/Core Identity): {day_p}
    - Time Pillar (Hidden Potential): {time_p}

    [Elemental Balance]
    {', '.join([f'{k}: {v}' for k, v in elements.items()])}

    [Key Traits]
    - Dominant Energy: {dominant[0]} ({dominant[1]})
    - Missing Energy: {', '.join(lacking) if lacking else 'None'}

    [Instructions for {theme.upper()} Analysis]
    {selected_instruction}

    [Tone]
    Empathetic, Insightful, Professional, Modern.
    Language: English (US Market).
    Output Format: Clean text with clear headings. No markdown bolding (**) excessively.
    """

    return prompt.strip()