import datetime


def calculate_next_time(
    now: datetime.datetime, interval_minutes: int
) -> datetime.datetime:
    """秒単位に切り捨てたタイムスタンプで次の時報の時刻を計算する"""
    interval_seconds = interval_minutes * 60
    now_timestamp_seconds = int(now.timestamp())
    next_timestamp = (
        (now_timestamp_seconds // interval_seconds) + 1
    ) * interval_seconds
    next_time = datetime.datetime.fromtimestamp(next_timestamp)
    return next_time
