import datetime


def iso_datetime():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def iso_to_beijing(iso: str, pattern: str = "%Y-%m-%d %H:%M:%S"):
    dt = datetime.datetime.strptime(iso, "%Y-%m-%dT%H:%M:%S.%f%z")
    return dt.astimezone(datetime.timezone(datetime.timedelta(hours=8))).strftime(pattern)
