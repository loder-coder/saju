from lunar_python import Lunar, Solar
from collections import Counter
from datetime import datetime

# 오행 매핑
FIVE_ELEMENTS = {
    "甲": "Wood", "乙": "Wood", "丙": "Fire", "丁": "Fire",
    "戊": "Earth", "己": "Earth", "庚": "Metal", "辛": "Metal",
    "壬": "Water", "癸": "Water",
    "寅": "Wood", "卯": "Wood", "巳": "Fire", "午": "Fire",
    "辰": "Earth", "戌": "Earth", "丑": "Earth", "未": "Earth",
    "申": "Metal", "酉": "Metal", "亥": "Water", "子": "Water"
}

# 십성(Ten Gods) 관계 매핑 (English Only)
# (User Element, Today Element) -> Relation
RELATIONS = {
    # 비겁 (Same Element)
    ("Wood", "Wood"): "Friend (Parallel)", ("Fire", "Fire"): "Friend (Parallel)",
    ("Earth", "Earth"): "Friend (Parallel)", ("Metal", "Metal"): "Friend (Parallel)",
    ("Water", "Water"): "Friend (Parallel)",

    # 식상 (Output)
    ("Wood", "Fire"): "Output (Expression)", ("Fire", "Earth"): "Output (Expression)",
    ("Earth", "Metal"): "Output (Expression)", ("Metal", "Water"): "Output (Expression)",
    ("Water", "Wood"): "Output (Expression)",

    # 재성 (Wealth)
    ("Wood", "Earth"): "Wealth (Goal)", ("Fire", "Metal"): "Wealth (Goal)",
    ("Earth", "Water"): "Wealth (Goal)", ("Metal", "Wood"): "Wealth (Goal)",
    ("Water", "Fire"): "Wealth (Goal)",

    # 관성 (Career/Power)
    ("Wood", "Metal"): "Career (Discipline)", ("Fire", "Water"): "Career (Discipline)",
    ("Earth", "Wood"): "Career (Discipline)", ("Metal", "Fire"): "Career (Discipline)",
    ("Water", "Earth"): "Career (Discipline)",

    # 인성 (Resource/Support)
    ("Wood", "Water"): "Resource (Support)", ("Fire", "Wood"): "Resource (Support)",
    ("Earth", "Fire"): "Resource (Support)", ("Metal", "Earth"): "Resource (Support)",
    ("Water", "Metal"): "Resource (Support)",
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


def calculate_saju(lunar_year: int, lunar_month: int, lunar_day: int, hour: int, minute: int):
    lunar = Lunar.fromYmdHms(lunar_year, lunar_month, lunar_day, hour, minute, 0)
    eight_char = lunar.getEightChar()

    saju_result = {
        "year": eight_char.getYearGan() + eight_char.getYearZhi(),
        "month": eight_char.getMonthGan() + eight_char.getMonthZhi(),
        "day": eight_char.getDayGan() + eight_char.getDayZhi(),
        "time": eight_char.getTimeGan() + eight_char.getTimeZhi()
    }

    return {
        "pillars": saju_result,
        "elements": analyze_elements(saju_result)
    }


def get_today_fortune(user_day_master_gan: str):
    """
    오늘의 운세 계산 (일진법)
    """
    # 오늘 날짜
    now = datetime.now()
    solar = Solar.fromYmd(now.year, now.month, now.day)
    lunar = solar.getLunar()

    # 오늘의 일진 (예: 甲子)
    today_gan = lunar.getEightChar().getDayGan()
    today_zhi = lunar.getEightChar().getDayZhi()

    user_elm = get_element(user_day_master_gan)
    today_elm = get_element(today_gan)

    relation = RELATIONS.get((user_elm, today_elm), "Unknown")

    # 간단한 점수 및 조언 로직
    score = 70  # 기본점수
    advice = ""

    if "Wealth" in relation:
        score = 90
        advice = "Excellent day for financial decisions!"
    elif "Resource" in relation:
        score = 85
        advice = "Great day for learning and receiving help."
    elif "Output" in relation:
        score = 80
        advice = "Good day for creativity and self-expression."
    elif "Friend" in relation:
        score = 75
        advice = "Good for networking, but watch out for competition."
    elif "Career" in relation:
        score = 60
        advice = "You might feel pressure today. Stay calm."

    return {
        "date": now.strftime("%Y-%m-%d"),
        "today_pillar": f"{today_gan}{today_zhi}",
        "user_element": user_elm,
        "today_element": today_elm,
        "relation": relation,
        "score": score,
        "advice": advice
    }