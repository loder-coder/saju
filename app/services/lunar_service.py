from lunar_python import Solar


def get_lunar_date(year: int, month: int, day: int) -> dict:
    solar = Solar.fromYmd(year, month, day)
    lunar = solar.getLunar()

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
            "isLeapMonth": lunar.isLeap()
        }
    }
