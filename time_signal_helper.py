import datetime

def calculate_next_time(now: datetime.datetime, interval_minutes: int) -> datetime.datetime:
    """指定された間隔（分）に基づいて、次の時報の時刻を計算する"""
    minutes = now.minute
    next_minute_target = ((minutes // interval_minutes) + 1) * interval_minutes
    next_hour = now.hour + (next_minute_target // 60)
    next_minute = next_minute_target % 60
    next_time = now.replace(hour=next_hour % 24, minute=next_minute, second=0, microsecond=0)
    if now >= next_time:
        next_time += datetime.timedelta(hours=1)
        next_time = next_time.replace(minute=next_minute, second=0, microsecond=0)
    return next_time
