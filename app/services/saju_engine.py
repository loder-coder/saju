from lunar_python import Lunar, Solar
from collections import Counter
from datetime import datetime

# 오행 매핑
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

# Flutter: SajuModel.rhythmKeyword
RHYTHM_KEYWORDS = {
    "Expression": "Creative",
    "Support": "Restorative",
    "Wealth": "Productive",
    "Friend": "Connected",
    "Career": "Focused",
}

ARCHETYPES = {
    "Wood": "The Pioneer",
    "Fire": "The Spark",
    "Earth": "The Anchor",
    "Metal": "The Architect",
    "Water": "The Voyager",
}

VISUAL_KEYWORDS = {
    "Friend": "balanced symmetry, connected network, soft teal light, mirrored surfaces, open gathering",
    "Expression": "creative studio, bold color splash, dynamic motion, vivid paint, expressive energy",
    "Wealth": "golden architecture, structured abundance, warm amber light, overflowing harvest, minimal luxury",
    "Career": "mountain ridge, geometric precision, cool blue steel, focused intensity, deliberate lines",
    "Support": "quiet library, deep roots, calm water, soft morning light, earthy textures",
}

PERIOD_ADVICE = {
    "daily": {
        "Wealth": "Execution energy is high today. Tackle a task you've been deferring — momentum is on your side.",
        "Support": "Absorption mode is active. Rest, reflect, and let new information settle. Learning sticks fast.",
        "Expression": "Your output flows naturally today. Share ideas without second-guessing. Authenticity lands well.",
        "Friend": "Social alignment is strong. Collaboration and honest conversation move faster than usual.",
        "Career": "Friction signals growth. Stay disciplined when things feel resistant — the resistance is productive.",
    },
    "weekly": {
        "Wealth": "This week rewards decisive action. Set one concrete goal and execute without over-planning.",
        "Support": "Invest in learning and in relationships that replenish you. Input before output.",
        "Expression": "Lead with your ideas this week. Creative output lands better than usual — ship it.",
        "Friend": "Peer energy aligns with yours. Group efforts and shared goals move fast.",
        "Career": "Challenges this week are calibrating you. Embrace the pressure and tighten your systems.",
    },
    "monthly": {
        "Wealth": "This month's theme is results. Convert accumulated plans into tangible deliverables.",
        "Support": "A restoration phase. Prioritize what sustains you — energy in before energy out.",
        "Expression": "Your authentic voice carries extra weight this month. Visibility is your edge.",
        "Friend": "Community and collaboration define this month. Build bridges, not just outcomes.",
        "Career": "This month challenges your structure. Refine your processes under pressure.",
    },
    "yearly": {
        "Wealth": "This year rewards builders. Tangible, real-world output defines your growth arc.",
        "Support": "A year of deepening foundations — mentors, deep learning, and quiet progress compound.",
        "Expression": "Your year of voice and visibility. Show up, share your perspective, and iterate.",
        "Friend": "A year to invest in relationships and shared missions. Who you build with matters.",
        "Career": "Growth through sustained challenge defines this year. Consistency beats intensity.",
    },
    "life": {
        "Wealth": "You're wired to produce and build. Your core energy converts vision into tangible reality — the builder archetype at its peak.",
        "Support": "Your deepest strength is absorption, wisdom, and being the foundation others build on. You empower from behind the scenes.",
        "Expression": "Your life force peaks when you create and share. Expression isn't optional for you — it's oxygen.",
        "Friend": "You thrive in resonance. Your deepest energy is relational and collaborative — find your tribe.",
        "Career": "You grow through challenge and mastery. Tension isn't a problem to solve — it's your engine.",
    },
}

YEAR_DESCRIPTIONS = {
    "Wealth": "A year of grounded execution. Your elemental energy creates momentum for tangible, lasting results. What you build now compounds quietly.",
    "Support": "A year of deepening roots. Invest in learning, mentorship, and relationships that replenish you. Quiet progress compounds invisibly.",
    "Expression": "A year of visibility and voice. Your natural inclination to create and share reaches its peak cycle. Show up consistently.",
    "Friend": "A year of alignment and collaboration. The people you invest in now will define your next chapter. Build with intention.",
    "Career": "A year of refinement under pressure. Challenges sharpen your edge — stay consistent. The friction is calibrating you.",
}


def get_element(char: str) -> str:
    return FIVE_ELEMENTS.get(char, "Unknown")


def analyze_elements(saju_dict: dict):
    elements = []
    for pillar in ["year", "month", "day", "time"]:
        if pillar in saju_dict:
            elements.append(get_element(saju_dict[pillar][0]))
            elements.append(get_element(saju_dict[pillar][1]))
    counts = Counter(elements)
    result = {"Wood": 0, "Fire": 0, "Earth": 0, "Metal": 0, "Water": 0}
    result.update(counts)
    return result


def get_dominant_element(elements: dict) -> str:
    return max(elements, key=elements.get)


def calculate_saju(year, month, day, hour, minute):
    solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
    lunar = solar.getLunar()
    eight = lunar.getEightChar()

    saju = {
        "year": eight.getYearGan() + eight.getYearZhi(),
        "month": eight.getMonthGan() + eight.getMonthZhi(),
        "day": eight.getDayGan() + eight.getDayZhi(),
        "time": eight.getTimeGan() + eight.getTimeZhi(),
    }

    return {"pillars": saju, "elements": analyze_elements(saju)}


def get_fortune_by_period(user_day_gan: str, period: str):
    """
    period: 'daily' | 'weekly' | 'monthly' | 'yearly' | 'life'
    """
    now = datetime.now()
    user_elm = get_element(user_day_gan)

    period_labels = {
        "daily": "Today's Rhythm",
        "weekly": "This Week's Rhythm",
        "monthly": f"{now.strftime('%B')}'s Pattern",
        "yearly": f"{now.year} Pattern",
        "life": "Life Theme",
    }
    label = period_labels.get(period, period.capitalize())

    if period == "life":
        relation = RELATIONS.get((user_elm, user_elm), "Friend")
        score = 80
    else:
        if period == "yearly":
            target_solar = Solar.fromYmd(now.year, 2, 4)
        elif period == "monthly":
            target_solar = Solar.fromYmd(now.year, now.month, 15)
        else:
            target_solar = Solar.fromYmd(now.year, now.month, now.day)

        eight = target_solar.getLunar().getEightChar()

        if period == "yearly":
            target_char = eight.getYearGan()
        elif period == "monthly":
            target_char = eight.getMonthGan()
        else:
            target_char = eight.getDayGan()

        target_elm = get_element(target_char)
        relation = RELATIONS.get((user_elm, target_elm), "Friend")

        score_base = {"Wealth": 92, "Support": 88, "Expression": 85, "Friend": 75, "Career": 65}
        date_seed = (now.year + now.month + now.day) % 10
        score = min(100, score_base.get(relation, 70) + date_seed - 5)

    # 연간 테마는 항상 yearly 기준으로 계산
    yearly_solar = Solar.fromYmd(now.year, 2, 4)
    yearly_eight = yearly_solar.getLunar().getEightChar()
    yearly_elm = get_element(yearly_eight.getYearGan())
    year_relation = RELATIONS.get((user_elm, yearly_elm), "Friend")

    insight = PERIOD_ADVICE.get(period, PERIOD_ADVICE["daily"]).get(relation, "Trust your process.")
    visual = VISUAL_KEYWORDS.get(relation, "soft mist, abstract forms, cinematic light")

    return {
        "period": label,
        "mode": relation.upper(),
        "score": score,
        "insight": insight,
        "rhythm_keyword": RHYTHM_KEYWORDS.get(relation, "Steady"),
        "year_theme": f"{now.year} Pattern",
        "year_description": YEAR_DESCRIPTIONS.get(year_relation, YEAR_DESCRIPTIONS["Friend"]),
        "image_keyword": f"{visual}, cinematic lighting, high quality, 8k",
    }
