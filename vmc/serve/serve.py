import os


def is_serve_enabled():
    return os.getenv("VMC_SERVE_ENABLED", "0") == "1"
