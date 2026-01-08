from lunar_python import Solar
import datetime
import pytz


def get_apparent_solar_time(year: int, month: int, day: int, hour: int, minute: int, timezone_str: str,
                            longitude: float):
    """
    입력받은 지역 표준시(Local Time)를 진태양시(Apparent Solar Time)로 변환
    """
    try:
        # 1. 입력받은 시간을 해당 Timezone의 datetime 객체로 생성
        tz = pytz.timezone(timezone_str)
        local_dt = tz.localize(datetime.datetime(year, month, day, hour, minute))

        # 2. UTC로 변환
        utc_dt = local_dt.astimezone(pytz.utc)

        # 3. 진태양시 보정 (Longitude Correction)
        # 태양은 1도 움직이는 데 4분 걸림.
        # UTC 기준 시간 + (경도 * 4분) = LMT (Local Mean Time)
        solar_correction_minutes = longitude * 4
        solar_dt = utc_dt + datetime.timedelta(minutes=solar_correction_minutes)

        return solar_dt.year, solar_dt.month, solar_dt.day, solar_dt.hour, solar_dt.minute

    except Exception as e:
        print(f"Time correction failed: {e}")
        # 실패 시 원본 그대로 리턴 (Fallback)
        return year, month, day, hour, minute


def get_lunar_date(year: int, month: int, day: int, hour: int, minute: int, timezone_str: str = "Asia/Seoul",
                   longitude: float = 127.0) -> dict:
    # 1. 진태양시로 시간 보정
    s_year, s_month, s_day, s_hour, s_minute = get_apparent_solar_time(
        year, month, day, hour, minute, timezone_str, longitude
    )

    # 2. 보정된 시간으로 Solar 객체 생성
    solar = Solar.fromYmdHms(s_year, s_month, s_day, s_hour, s_minute, 0)
    lunar = solar.getLunar()

    # 윤달 여부 안전 처리
    try:
        is_leap = lunar.isLeapMonth()
    except:
        is_leap = False

    return {
        "solar": {
            "year": s_year,
            "month": s_month,
            "day": s_day,
            "hour": s_hour,
            "minute": s_minute,
            "original": {
                "year": year, "month": month, "day": day, "hour": hour, "minute": minute
            }
        },
        "lunar": {
            "year": lunar.getYear(),
            "month": lunar.getMonth(),
            "day": lunar.getDay(),
            "isLeapMonth": is_leap
        }
    }