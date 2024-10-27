def trunctuate_string(string, max_length=100, suffix="...", side: str = "right"):
    if len(string) > max_length:
        if side == "left":
            return suffix + string[-max_length:]
        elif side == "right":
            return string[:max_length] + suffix
        else:
            return string[: max_length // 2] + suffix + string[-max_length // 2 :]
    else:
        return string
