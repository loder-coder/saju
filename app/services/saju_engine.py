from lunar_python import Lunar


def calculate_saju(lunar_year: int, lunar_month: int, lunar_day: int, hour: int, minute: int):
    # 시간 포함해서 Lunar 생성
    lunar = Lunar.fromYmdHms(lunar_year, lunar_month, lunar_day, hour, minute, 0)
    eight_char = lunar.getEightChar()

    return {
        "year": eight_char.getYearGan() + eight_char.getYearZhi(),
        "month": eight_char.getMonthGan() + eight_char.getMonthZhi(),
        "day": eight_char.getDayGan() + eight_char.getDayZhi(),
        "time": eight_char.getTimeGan() + eight_char.getTimeZhi()
    }
