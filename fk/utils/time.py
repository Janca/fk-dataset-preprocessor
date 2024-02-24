def format_timedelta(start: float, end: float) -> str:
    delta = end - start

    sec = delta
    hours = sec // 3600
    minutes = (sec // 60) % 60  # Use modulo to get remaining minutes after dividing by 60
    seconds = sec % 60  # Use modulo to get remaining seconds after removing minutes

    return f'{hours:02f}:{minutes:02f}:{seconds:02f}'
