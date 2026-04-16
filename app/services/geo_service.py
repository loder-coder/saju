import os
import googlemaps
from datetime import datetime
from functools import lru_cache
from dotenv import load_dotenv

# 로컬 개발 환경을 위해 .env 로드
load_dotenv()


class GeoService:
    def __init__(self):
        # Koyeb 환경변수 또는 .env에서 키를 가져옴
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        self.client = None

        print("--- [GeoService] Initializing ---")
        if self.api_key:
            try:
                self.client = googlemaps.Client(key=self.api_key)
                print(f"✅ Google Maps API Key loaded: {self.api_key[:5]}...")
            except Exception as e:
                print(f"❌ Failed to initialize Google Maps Client: {e}")
        else:
            print("⚠️  GOOGLE_MAPS_API_KEY is missing. Defaulting to Seoul (KST).")

    @lru_cache(maxsize=2048)
    def get_location_info(self, query: str):
        """
        도시 이름(query) -> {address, lat, lng, timezone} 반환
        """
        if not self.client:
            return None

        try:
            print(f"🔍 Geo-searching for: {query}")

            # 1. Geocoding (장소 -> 좌표)
            geocode_result = self.client.geocode(query)

            if not geocode_result:
                print(f"❌ Location not found: {query}")
                return None

            result = geocode_result[0]
            location = result['geometry']['location']
            lat = location['lat']
            lng = location['lng']
            formatted_address = result.get('formatted_address', query)

            # 2. Timezone (좌표 -> 시간대 ID)
            # timestamp=현재시간
            tz_result = self.client.timezone((lat, lng), timestamp=datetime.now().timestamp())
            time_zone_id = tz_result.get('timeZoneId')  # 예: "Europe/Paris"

            if not time_zone_id:
                return None

            print(f"✅ Resolved: {formatted_address} -> {time_zone_id} ({lat}, {lng})")

            return {
                "address": formatted_address,
                "latitude": lat,
                "longitude": lng,
                "timezone": time_zone_id
            }

        except Exception as e:
            print(f"❌ GeoService Error: {e}")
            return None


# 싱글톤 객체 생성
geo_service = GeoService()