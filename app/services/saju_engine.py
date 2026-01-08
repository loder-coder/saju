from lunar_python import Lunar
from collections import Counter

# 오행 매핑 데이터 (Global Service용 English)
FIVE_ELEMENTS = {
    # 천간 (Heavenly Stems)
    "甲": "Wood", "乙": "Wood",
    "丙": "Fire", "丁": "Fire",
    "戊": "Earth", "己": "Earth",
    "庚": "Metal", "辛": "Metal",
    "壬": "Water", "癸": "Water",

    # 지지 (Earthly Branches)
    "寅": "Wood", "卯": "Wood",
    "巳": "Fire", "午": "Fire",
    "辰": "Earth", "戌": "Earth", "丑": "Earth", "未": "Earth",
    "申": "Metal", "酉": "Metal",
    "亥": "Water", "子": "Water"
}


def get_element(hanja_char: str) -> str:
    return FIVE_ELEMENTS.get(hanja_char, "Unknown")


def analyze_elements(saju_dict: dict):
    """
    사주 8글자를 받아서 오행 개수와 비율을 분석함
    """
    elements = []

    # 8글자 분해 (예: "戊寅" -> "戊", "寅")
    for pillar in ["year", "month", "day", "time"]:
        char_gan = saju_dict[pillar][0]  # 천간
        char_zhi = saju_dict[pillar][1]  # 지지

        elements.append(get_element(char_gan))
        elements.append(get_element(char_zhi))

    # 개수 세기
    counts = Counter(elements)

    # 기본 5행 0으로 초기화 (없는 오행도 표시해줘야 함)
    result = {
        "Wood": 0, "Fire": 0, "Earth": 0, "Metal": 0, "Water": 0
    }
    result.update(counts)

    return result


def calculate_saju(lunar_year: int, lunar_month: int, lunar_day: int, hour: int, minute: int):
    # 시간 포함해서 Lunar 생성
    lunar = Lunar.fromYmdHms(lunar_year, lunar_month, lunar_day, hour, minute, 0)
    eight_char = lunar.getEightChar()

    saju_result = {
        "year": eight_char.getYearGan() + eight_char.getYearZhi(),
        "month": eight_char.getMonthGan() + eight_char.getMonthZhi(),
        "day": eight_char.getDayGan() + eight_char.getDayZhi(),
        "time": eight_char.getTimeGan() + eight_char.getTimeZhi()
    }

    # 오행 분석 실행
    analysis = analyze_elements(saju_result)

    return {
        "pillars": saju_result,
        "elements": analysis
    }