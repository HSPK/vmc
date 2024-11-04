from typing import Any, Callable


class LazyObjProxy:
    def __init__(self, func: Callable[[], Any]):
        self._instance = None
        self._factory = func

    def _load_instance(self) -> Any:
        if self._instance is None:
            self._instance = self._factory()
        return self._instance

    def __getattr__(self, name):
        self._load_instance()
        return getattr(self._instance, name)

    def __setattr__(self, name, value):
        """Load the actual object and delegate attribute setting."""
        if name in ("_factory", "_instance"):
            super().__setattr__(name, value)
        else:
            self._load_instance()
            setattr(self._instance, name, value)

    def __delattr__(self, name):
        """Load the actual object and delegate attribute deletion."""
        self._load_instance()
        delattr(self._instance, name)

    def __call__(self, *args, **kwargs):
        """Allow the proxy to behave like a callable if the underlying object is callable."""
        self._load_instance()
        return self._instance(*args, **kwargs)

    def __repr__(self):
        """Represent the proxy with details about its load state."""
        if self._instance is None:
            return f"<LazyObjectProxy(unloaded, factory={self._factory})>"
        return repr(self._instance)

    def __instancecheck__(self, instance):
        return isinstance(self._load_instance, instance)

    def __class__(self):
        return self._load_instance.__class__

    def __getitem__(self, item):
        self._load_instance()
        return self._instance[item]

    def __setitem__(self, key, value):
        self._load_instance()
        self._instance[key] = value
