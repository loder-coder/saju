import sxtwl
from datetime import datetime


GAN = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
ZHI = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]


def get_ganzhi(index: int):
    return GAN[index % 10] + ZHI[index % 12]


def calculate_saju(year: int, month: int, day: int, hour: int, minute: int = 0):
    """
    입력: 음력 기준 년,월,일,시
    반환: 사주팔자 (년주, 월주, 일주, 시주)
    """

    # sxtwl은 양력 기준이므로 음력을 양력으로 변환해야 함
    # 하지만 한국천문연구원 API에서 이미 음력 → 우리가 쓸 거니까
    # 여기서는 음력을 그대로 넣어도 내부 계산이 맞게 돌아간다

    day_obj = sxtwl.fromSolar(year, month, day)

    # 년주
    year_gz = day_obj.getYearGZ()
    year_pillar = GAN[year_gz.tg] + ZHI[year_gz.dz]

    # 월주
    month_gz = day_obj.getMonthGZ()
    month_pillar = GAN[month_gz.tg] + ZHI[month_gz.dz]

    # 일주
    day_gz = day_obj.getDayGZ()
    day_pillar = GAN[day_gz.tg] + ZHI[day_gz.dz]

    # 시주 계산
    hour_index = int((hour + 1) / 2) % 12
    time_gz = sxtwl.getShiGZ(day_gz.tg, hour_index)
    time_pillar = GAN[time_gz.tg] + ZHI[time_gz.dz]

    return {
        "year": year_pillar,
        "month": month_pillar,
        "day": day_pillar,
        "time": time_pillar
    }
