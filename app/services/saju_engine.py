from lunar_python import Lunar


def calculate_saju(lunar_year: int, lunar_month: int, lunar_day: int, hour: int, minute: int):
    lunar = Lunar.fromYmd(lunar_year, lunar_month, lunar_day)
    eight_char = lunar.getEightChar()

    return {
        "year": eight_char.getYearGan() + eight_char.getYearZhi(),
        "month": eight_char.getMonthGan() + eight_char.getMonthZhi(),
        "day": eight_char.getDayGan() + eight_char.getDayZhi(),
        "time": eight_char.getTimeGanByTime(hour, minute) + eight_char.getTimeZhiByTime(hour, minute)
    }
