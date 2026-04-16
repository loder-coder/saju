GAN_EN = {
    "甲": "Yang Wood", "乙": "Yin Wood", "丙": "Yang Fire", "丁": "Yin Fire",
    "戊": "Yang Earth", "己": "Yin Earth", "庚": "Yang Metal", "辛": "Yin Metal",
    "壬": "Yang Water", "癸": "Yin Water"
}

ZHI_EN = {
    "子": "Rat", "丑": "Ox", "寅": "Tiger", "卯": "Rabbit",
    "辰": "Dragon", "巳": "Snake", "午": "Horse", "未": "Sheep",
    "申": "Monkey", "酉": "Rooster", "戌": "Dog", "亥": "Pig"
}

ZHI_ELEMENT = {
    "子": "Water", "丑": "Earth", "寅": "Wood", "卯": "Wood",
    "辰": "Earth", "巳": "Fire", "午": "Fire", "未": "Earth",
    "申": "Metal", "酉": "Metal", "戌": "Earth", "亥": "Water"
}


def translate_pillar(gan_zhi: str) -> str:
    if len(gan_zhi) != 2:
        return gan_zhi
    gan = GAN_EN.get(gan_zhi[0], gan_zhi[0])
    zhi = ZHI_EN.get(gan_zhi[1], gan_zhi[1])
    return f"{gan} / {zhi}"


def build_saju_prompt(saju_data: dict, theme: str = "general") -> str:
    pillars = saju_data.get("saju", {}).get("pillars", {})
    elements = saju_data.get("saju", {}).get("elements", {})

    day_raw = pillars.get("day", "")
    core_identity = translate_pillar(day_raw) if day_raw else "Unknown"

    sorted_elements = sorted(elements.items(), key=lambda x: x[1], reverse=True)
    dominant = sorted_elements[0][0] if sorted_elements else "Unknown"
    lacking = [k for k, v in elements.items() if v == 0]
    balance_str = ", ".join(f"{k}: {v}" for k, v in elements.items())

    theme_focus = {
        "general": "Overall personality strengths, blind spots, and life direction.",
        "love": "Relational style, emotional patterns, and compatibility tendencies.",
        "career": "Professional strengths, optimal work environment, and growth strategy.",
        "wealth": "Financial decision-making patterns, risk tolerance, and abundance mindset.",
    }
    focus = theme_focus.get(theme, theme_focus["general"])

    prompt = f"""
You are a personality and behavioral analyst specializing in Elemental Profile Assessment.
Analyze the following user profile and deliver a sharp, modern insight report.

[Elemental Profile]
- Core Identity Type: {core_identity}
- Elemental Balance: {balance_str}
- Dominant Element: {dominant}
- Underdeveloped Element(s): {', '.join(lacking) if lacking else 'None — well-rounded profile'}

[Analysis Focus: {theme.upper()}]
{focus}

[Output Format — follow strictly]
### OVERVIEW
Exactly 3 bullet points. Each must start with an emoji, a **Bold Keyword**, then one punchy sentence.
Example:
- 🔥 **Drive-First Thinker**: You act before you overthink — decisive under pressure.
- 🌊 **Depth Over Surface**: Your instincts outperform your stated logic.
- ⚖️ **Calibration Gap**: Your biggest blind spot is knowing when to pause.

### DEEP DIVE
Under 200 words. Concrete, grounded analysis based strictly on the profile above.
No generic advice. Speak to this specific elemental pattern.

[Tone]
Sharp, modern, like a top-tier executive coach. No mystical language. English only.
""".strip()

    return prompt
