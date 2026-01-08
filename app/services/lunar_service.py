from lunar_python import Solar


def get_lunar_date(year: int, month: int, day: int) -> dict:
    solar = Solar.fromYmd(year, month, day)
    lunar = solar.getLunar()

    # 윤달 여부 안전 처리
    try:
        is_leap = lunar.isLeapMonth()
    except:
        is_leap = False

    return {
        "solar": {
            "year": year,
            "month": month,
            "day": day
        },
        "lunar": {
            "year": lunar.getYear(),
            "month": lunar.getMonth(),
            "day": lunar.getDay(),
            "isLeapMonth": is_leap
        }
    }
