from lunar_python import Lunar


def calculate_saju(lunar_year: int, lunar_month: int, lunar_day: int, hour: int, minute: int):
    lunar = Lunar.fromYmd(lunar_year, lunar_month, lunar_day)

    eight_char = lunar.getEightChar()

    year_gan = eight_char.getYearGan()
    year_zhi = eight_char.getYearZhi()

    month_gan = eight_char.getMonthGan()
    month_zhi = eight_char.getMonthZhi()

    day_gan = eight_char.getDayGan()
    day_zhi = eight_char.getDayZhi()

    time_zhi = eight_char.getTimeZhiByTime(hour, minute)
    time_gan = eight_char.getTimeGanByTime(hour, minute)

    return {
        "year": f"{year_gan}{year_zhi}",
        "month": f"{month_gan}{month_zhi}",
        "day": f"{day_gan}{day_zhi}",
        "time": f"{time_gan}{time_zhi}"
    }
