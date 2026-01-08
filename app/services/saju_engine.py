from lunar_python import Lunar, Solar
from collections import Counter
from datetime import datetime, timedelta

# 오행 및 십성 매핑 (영어)
FIVE_ELEMENTS = {
    "甲": "Wood", "乙": "Wood", "丙": "Fire", "丁": "Fire", "戊": "Earth",
    "己": "Earth", "庚": "Metal", "辛": "Metal", "壬": "Water", "癸": "Water",
    "寅": "Wood", "卯": "Wood", "巳": "Fire", "午": "Fire", "辰": "Earth",
    "戌": "Earth", "丑": "Earth", "未": "Earth", "申": "Metal", "酉": "Metal",
    "亥": "Water", "子": "Water"
}

RELATIONS = {
    ("Wood", "Wood"): "Friend", ("Wood", "Fire"): "Expression", ("Wood", "Earth"): "Wealth",
    ("Wood", "Metal"): "Career", ("Wood", "Water"): "Support",
    ("Fire", "Fire"): "Friend", ("Fire", "Earth"): "Expression", ("Fire", "Metal"): "Wealth",
    ("Fire", "Water"): "Career", ("Fire", "Wood"): "Support",
    ("Earth", "Earth"): "Friend", ("Earth", "Metal"): "Expression", ("Earth", "Water"): "Wealth",
    ("Earth", "Wood"): "Career", ("Earth", "Fire"): "Support",
    ("Metal", "Metal"): "Friend", ("Metal", "Water"): "Expression", ("Metal", "Wood"): "Wealth",
    ("Metal", "Fire"): "Career", ("Metal", "Earth"): "Support",
    ("Water", "Water"): "Friend", ("Water", "Wood"): "Expression", ("Water", "Fire"): "Wealth",
    ("Water", "Earth"): "Career", ("Water", "Metal"): "Support",
}

# 이미지 생성을 위한 비주얼 키워드 매핑
VISUAL_KEYWORDS = {
    "Friend": "forest gathering, harmony, mirror reflection, twin souls, mystical teal light",
    "Expression": "blooming flowers, creative splash, phoenix rising, vibrant art, dynamic motion",
    "Wealth": "golden coins, treasure chest, luxurious palace, overflowing harvest, golden light",
    "Career": "tall mountain peak, iron throne, structured geometry, chess board, blue icy focus",
    "Support": "ancient library, cozy shelter, mother earth, flowing river, warm lantern light"
}


def get_element(char: str) -> str:
    return FIVE_ELEMENTS.get(char, "Unknown")


def analyze_elements(saju_dict: dict):
    elements = []
    for pillar in ["year", "month", "day", "time"]:
        elements.append(get_element(saju_dict[pillar][0]))
        elements.append(get_element(saju_dict[pillar][1]))
    counts = Counter(elements)
    result = {"Wood": 0, "Fire": 0, "Earth": 0, "Metal": 0, "Water": 0}
    result.update(counts)
    return result


def calculate_saju(lunar_year, lunar_month, lunar_day, hour, minute):
    lunar = Lunar.fromYmdHms(lunar_year, lunar_month, lunar_day, hour, minute, 0)
    eight = lunar.getEightChar()
    saju = {
        "year": eight.getYearGan() + eight.getYearZhi(),
        "month": eight.getMonthGan() + eight.getMonthZhi(),
        "day": eight.getDayGan() + eight.getDayZhi(),
        "time": eight.getTimeGan() + eight.getTimeZhi()
    }
    return {"pillars": saju, "elements": analyze_elements(saju)}


def get_fortune_by_period(user_day_gan: str, period: str):
    """
    기간별 운세 로직
    period: 'daily', 'weekly', 'monthly', 'yearly'
    """
    now = datetime.now()
    user_elm = get_element(user_day_gan)

    # 1. 비교 대상 날짜/연도 설정
    if period == 'yearly':
        # 올해의 입춘 기준 (간략화: 현재 연도)
        target_solar = Solar.fromYmd(now.year, 2, 4)
        period_name = f"{now.year} Flow"
    elif period == 'monthly':
        target_solar = Solar.fromYmd(now.year, now.month, 15)  # 월 중간값
        period_name = f"{now.strftime('%B')} Flow"
    elif period == 'weekly':
        target_solar = Solar.fromYmd(now.year, now.month, now.day + 3)  # 주 중간값
        period_name = "This Week's Flow"
    else:  # daily
        target_solar = Solar.fromYmd(now.year, now.month, now.day)
        period_name = "Today's Flow"

    lunar = target_solar.getLunar()
    eight = lunar.getEightChar()

    # 2. 비교 대상 글자 (운세의 주체)
    if period == 'yearly':
        target_char = eight.getYearGan()  # 세운 천간
    elif period == 'monthly':
        target_char = eight.getMonthGan()  # 월운 천간
    else:
        target_char = eight.getDayGan()  # 일운 천간

    target_elm = get_element(target_char)
    relation = RELATIONS.get((user_elm, target_elm), "Unknown")

    # 3. 점수 및 키워드 생성
    score_map = {"Wealth": 92, "Support": 88, "Expression": 85, "Friend": 75, "Career": 65}
    score = score_map.get(relation, 70)

    # 랜덤성을 위해 날짜 기반 미세 조정
    date_seed = (now.year + now.month + now.day) % 10
    final_score = min(100, score + date_seed - 5)

    visual_prompt = VISUAL_KEYWORDS.get(relation, "mystical fog, mystery, stars")

    # 조언
    advices = {
        "Wealth": "Focus on results. Abundance is near.",
        "Support": "A good time to learn and rest.",
        "Expression": "Show your talent. Be bold.",
        "Friend": "Connect with others, but stay independent.",
        "Career": "Face challenges calmly. Discipline is key."
    }

    return {
        "period": period_name,
        "relation_title": relation.upper(),
        "score": final_score,
        "advice": advices.get(relation, "Trust your intuition."),
        "image_keyword": f"{visual_prompt}, cinematic lighting, high quality, 8k, oriental fantasy style"
    }