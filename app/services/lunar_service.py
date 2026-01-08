import os
import requests


LUNAR_API_URL = os.getenv("LUNAR_API_URL")
LUNAR_API_KEY = os.getenv("LUNAR_API_KEY")


class LunarServiceError(Exception):
    pass


def get_lunar_date(year: int, month: int, day: int) -> dict:
    if not LUNAR_API_URL or not LUNAR_API_KEY:
        raise LunarServiceError("LUNAR_API_URL or LUNAR_API_KEY not set")

    params = {
        "serviceKey": LUNAR_API_KEY,
        "solYear": str(year),
        "solMonth": str(month).zfill(2),
        "solDay": str(day).zfill(2),
        "_type": "json"
    }

    try:
        response = requests.get(LUNAR_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        raise LunarServiceError(f"Failed to call lunar API: {str(e)}")

    try:
        body = data["response"]["body"]
        items = body.get("items")

        if not items or items == "":
            raise LunarServiceError(f"No lunar data for date: {year}-{month}-{day}")

        item = items["item"]

    except Exception as e:
        raise LunarServiceError(f"Invalid response structure or empty data: {data}")

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
            "isLeapMonth": True if item["lunLeapmonth"] == "1" else False
        }
    }
