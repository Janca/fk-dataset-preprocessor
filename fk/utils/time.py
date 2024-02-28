def format_timedelta(start: float, end: float) -> str:
    delta = end - start

    sec = delta
    hours = int(sec // 3600)
    minutes = int((sec // 60) % 60)
    seconds = int(sec % 60)

    return f'{hours:02d}:{minutes:02d}:{seconds:02d}'
