from lunar_python import Lunar, Solar
from collections import Counter

# 오행 매핑
FIVE_ELEMENTS = {
    "甲": "Wood", "乙": "Wood", "丙": "Fire", "丁": "Fire",
    "戊": "Earth", "己": "Earth", "庚": "Metal", "辛": "Metal",
    "壬": "Water", "癸": "Water",
    "寅": "Wood", "卯": "Wood", "巳": "Fire", "午": "Fire",
    "辰": "Earth", "戌": "Earth", "丑": "Earth", "未": "Earth",
    "申": "Metal", "酉": "Metal", "亥": "Water", "子": "Water"
}

TEN_GODS = {
    # 간단한 십성(Ten Gods) 로직: 아생자(식상), 아극자(재성) 등
    # 실제로는 음양까지 따져야 하지만 MVP용으로 오행 관계만 정의
    ("Wood", "Wood"): "Friend (비겁)", ("Wood", "Fire"): "Output (식상)",
    ("Wood", "Earth"): "Wealth (재성)", ("Wood", "Metal"): "Career (관성)", ("Wood", "Water"): "Support (인성)",

    ("Fire", "Fire"): "Friend (비겁)", ("Fire", "Earth"): "Output (식상)",
    ("Fire", "Metal"): "Wealth (재성)", ("Fire", "Water"): "Career (관성)", ("Fire", "Wood"): "Support (인성)",

    ("Earth", "Earth"): "Friend (비겁)", ("Earth", "Metal"): "Output (식상)",
    ("Earth", "Water"): "Wealth (재성)", ("Earth", "Wood"): "Career (관성)", ("Earth", "Fire"): "Support (인성)",

    ("Metal", "Metal"): "Friend (비겁)", ("Metal", "Water"): "Output (식상)",
    ("Metal", "Wood"): "Wealth (재성)", ("Metal", "Fire"): "Career (관성)", ("Metal", "Earth"): "Support (인성)",

    ("Water", "Water"): "Friend (비겁)", ("Water", "Wood"): "Output (식상)",
    ("Water", "Fire"): "Wealth (재성)", ("Water", "Earth"): "Career (관성)", ("Water", "Metal"): "Support (인성)",
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


def get_today_fortune(user_day_master_gan: str, target_date_str: str):
    """
    오늘의 운세 로직 (일진법)
    :param user_day_master_gan: 사용자의 일간 (예: 甲)
    :param target_date_str: 오늘 날짜 (YYYY-MM-DD)
    """
    y, m, d = map(int, target_date_str.split("-"))
    solar = Solar.fromYmd(y, m, d)
    lunar = solar.getLunar()
    day_ganzhi = lunar.getEightChar().getDayGan() + lunar.getEightChar().getDayZhi()

    today_gan = day_ganzhi[0]  # 오늘 천간
    today_zhi = day_ganzhi[1]  # 오늘 지지

    user_elm = get_element(user_day_master_gan)
    today_elm = get_element(today_gan)

    relation = TEN_GODS.get((user_elm, today_elm), "Unknown")

    return {
        "date": target_date_str,
        "today_pillar": day_ganzhi,  # 예: 庚申
        "energy": today_elm,  # 예: Metal
        "relation": relation,  # 예: Career (관성) - 직장운/스트레스
        "score": 80 if "Wealth" in relation or "Support" in relation else 50
    }