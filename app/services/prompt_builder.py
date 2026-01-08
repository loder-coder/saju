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


def build_saju_prompt(saju_data: dict) -> str:
    """
    JSON 결과를 받아서 LLM에게 던질 영어 프롬프트를 생성함
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

    # 3. 프롬프트 구성 (System Persona + Data Context)
    prompt = f"""
    You are an expert 'Life Consultant' who uses Eastern philosophy (Five Elements) to analyze personality and potential. 
    Do NOT act like a fortune teller or mystic. Act like a modern MBTI analyst or psychology counselor.

    Analyze the following user's 'Energy Blueprint':

    [User Profile]
    - Year Pillar (Social/Roots): {year_p}
    - Month Pillar (Career/Environment): {month_p}
    - Day Pillar (Self/Core Identity): {day_p}
    - Time Pillar (Hidden Potential): {time_p}

    [Elemental Balance]
    {', '.join([f'{k}: {v}' for k, v in elements.items()])}

    [Key Traits]
    - Dominant Energy: {dominant[0]} (Count: {dominant[1]}) -> Explain what having strong '{dominant[0]}' energy means for their personality.
    - Missing Energy: {', '.join(lacking) if lacking else 'None'} -> Explain the potential weakness or what they seek in life.

    [Instructions]
    1. Define their 'Core Archetype' based on the Day Pillar ({day_p}).
    2. Explain their strength based on the Dominant Energy.
    3. Give 1 practical piece of advice for career or relationships based on the Missing Energy.
    4. Tone: Empathetic, Insightful, Professional, Modern.
    5. Language: English (US Market).
    """

    return prompt.strip()


# 테스트용 실행 코드 (나중에 삭제)
if __name__ == "__main__":
    test_data = {
        "saju": {
            "pillars": {"year": "戊寅", "month": "壬戌", "day": "庚寅", "time": "丁亥"},
            "elements": {"Wood": 2, "Fire": 1, "Earth": 2, "Metal": 1, "Water": 2}
        }
    }
    print(build_saju_prompt(test_data))