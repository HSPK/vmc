import arrow


def get_current_date_formatted(format: str = "YYYY-MM-DD HH:mm:ss") -> str:
    return arrow.now(tz="Asia/Shanghai").format(format)
