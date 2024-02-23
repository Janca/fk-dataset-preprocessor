import datetime


def format_timedelta(start: float, end: float) -> str:
    delta = datetime.timedelta(0, end - start)

    sec = delta.seconds
    hours = sec // 3600
    minutes = (sec // 60) - (hours * 60)

    return f'{hours:02d}:{minutes:02d}:{sec:02d}'
