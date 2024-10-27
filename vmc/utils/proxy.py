import os
import warnings


class use_proxy:
    def __enter__(self):
        if os.getenv("http_proxy") or os.getenv("https_proxy"):
            warnings.warn("http_proxy or https_proxy already set, overriding")
        os.environ["http_proxy"] = os.getenv("_HTTP_PROXY")
        os.environ["https_proxy"] = os.getenv("_HTTP_PROXY")
        return self

    def __exit__(self, *args):
        os.environ.pop("http_proxy")
        os.environ.pop("https_proxy")
