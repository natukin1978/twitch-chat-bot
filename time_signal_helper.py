import datetime

def calculate_next_time(now: datetime.datetime, interval_minutes: int) -> datetime.datetime:
    """指定された間隔（分）に基づいて、次の時報の時刻を計算する（分単位で処理）"""
    total_minutes = now.hour * 60 + now.minute
    next_total_minutes = ((total_minutes // interval_minutes) + 1) * interval_minutes
    next_hour = (next_total_minutes // 60) % 24
    next_minute = next_total_minutes % 60
    next_time = now.replace(hour=next_hour, minute=next_minute, second=0, microsecond=0)
    return next_time
