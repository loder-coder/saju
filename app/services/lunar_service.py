import os
import requests
import xmltodict

LUNAR_API_URL = os.getenv("LUNAR_API_URL")
LUNAR_API_KEY = os.getenv("LUNAR_API_KEY")


class LunarServiceError(Exception):
    pass


def get_lunar_date(year: int, month: int, day: int) -> dict:
    if not LUNAR_API_URL or not LUNAR_API_KEY:
        raise LunarServiceError("LUNAR_API_URL or LUNAR_API_KEY not set in environment variables")

    params = {
        "serviceKey": LUNAR_API_KEY,
        "solYear": str(year),
        "solMonth": f"{month:02d}",
        "solDay": f"{day:02d}"
    }

    try:
        response = requests.get(LUNAR_API_URL, params=params, timeout=10)
        response.raise_for_status()
    except Exception as e:
        raise LunarServiceError(f"Failed to call lunar API: {str(e)}")

    raw = response.text

    try:
        # 1. JSON 먼저 시도
        if raw.strip().startswith("{"):
            data = response.json()
        else:
            # 2. 아니면 XML 파싱
            data = xmltodict.parse(raw)
    except Exception as e:
        raise LunarServiceError(f"Failed to parse lunar API response: {str(e)}")

    try:
        body = data["response"]["body"]

        if not body.get("items"):
            raise LunarServiceError(f"No lunar data for date: {year}-{month}-{day}")

        item = body["items"]["item"]

        return {
            "solar": {
                "year": year,
                "month": month,
                "day": day
            },
            "lunar": {
                "year": int(item["lunYear"]),
                "month": int(item["lunMonth"]),
                "day": int(item["lunDay"]),
                "isLeapMonth": item.get("lunLeapmonth") in ["1", "윤"]
            }
        }

    except LunarServiceError:
        raise
    except Exception:
        raise LunarServiceError(f"Invalid response structure: {data}")
