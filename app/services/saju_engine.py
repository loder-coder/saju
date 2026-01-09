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
    """천간/지지 글자를 받아 오행(Wood, Fire 등)을 반환"""
    return FIVE_ELEMENTS.get(char, "Unknown")


def analyze_elements(saju_dict: dict):
    """사주 팔자(4기둥)에서 오행 개수를 세어 반환"""
    elements = []
    # saju_dict["year"] 등은 "甲子" 처럼 2글자 문자열임
    for pillar in ["year", "month", "day", "time"]:
        if pillar in saju_dict:
            gan = saju_dict[pillar][0]  # 천간
            zhi = saju_dict[pillar][1]  # 지지
            elements.append(get_element(gan))
            elements.append(get_element(zhi))

    counts = Counter(elements)
    result = {"Wood": 0, "Fire": 0, "Earth": 0, "Metal": 0, "Water": 0}
    result.update(counts)
    return result


def calculate_saju(year, month, day, hour, minute):
    """
    만세력 계산 핵심 함수

    [변경 사항]
    기존에는 Lunar(음력) 객체를 생성했으나, '윤달' 여부를 파라미터로 받지 않아 정확도가 떨어질 수 있음.
    lunar_service에서 이미 '진태양시(Apparent Solar Time)'로 보정된 양력(Solar) 시간을 구했으므로,
    이를 이용해 Solar 객체로부터 사주를 뽑는 것이 가장 정확하고 안전함.

    :param year: 보정된 양력 연도 (lunar['solar']['year'])
    :param month: 보정된 양력 월 (lunar['solar']['month'])
    :param day: 보정된 양력 일 (lunar['solar']['day'])
    :param hour: 보정된 양력 시 (lunar['solar']['hour'])
    :param minute: 보정된 양력 분 (lunar['solar']['minute'])
    """
    # 1. 보정된 양력 시간으로 Solar 객체 생성 (이게 만세력 기준이 됨)
    solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)

    # 2. Solar -> Lunar(절기 포함) 변환
    # Solar 객체에서 getLunar()를 호출하면 절기와 윤달이 자동 계산된 Lunar 객체를 얻음
    lunar = solar.getLunar()

    # 3. 사주 팔자 추출
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
    user_day_gan: 사용자의 일간 (예: '甲')
    """
    now = datetime.now()
    user_elm = get_element(user_day_gan)

    # 1. 비교 대상 날짜/연도 설정
    if period == 'yearly':
        # 입춘 기준 대략적 처리 (정확한 절입시간 계산은 복잡하므로 2/4일 고정)
        target_solar = Solar.fromYmd(now.year, 2, 4)
        period_name = f"{now.year} Flow"
    elif period == 'monthly':
        target_solar = Solar.fromYmd(now.year, now.month, 15)
        period_name = f"{now.strftime('%B')} Flow"
    elif period == 'weekly':
        target_solar = Solar.fromYmd(now.year, now.month, now.day)  # 주간은 오늘 기준
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

    # 날짜 기반 랜덤성 추가 (매일/매년 조금씩 다르게)
    date_seed = (now.year + now.month + now.day) % 10
    final_score = min(100, score + date_seed - 5)

    visual_prompt = VISUAL_KEYWORDS.get(relation, "mystical fog, mystery, stars")

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