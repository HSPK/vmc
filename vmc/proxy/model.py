import asyncio
import random
import time
from enum import Enum

import vmc.models as api_module
from vmc.models import VMC
from vmc.types.model_config import ModelConfig


class Algorithm(Enum):
    RANDOM = "random"
    ROUND_ROBIN = "round_robin"
    LEAST_BUSY = "least_busy"
    PRIORITY = "priority"
    BUDGET = "budget"


class RateLimiter:
    def __init__(self, rate: int, period: int):
        self.rate = rate
        self.period = period
        self._count = 0
        self._last = time.time()
        self.next_available_wait_time = 0

    def __call__(self):
        if self.rate == 0 or self.period == 0:
            return True
        now = time.time()
        if now - self._last > self.period:
            self._count = 0
            self._last = now
        if self._count < self.rate:
            self._count += 1
            return True
        self.next_available_wait_time = self.period - (now - self._last)
        return False


class ProxyModel:
    def __init__(
        self,
        model: ModelConfig,
        credentials: list[dict] | None = None,
        init_kwargs: dict | None = None,
        rate: int = 0,
        period: int = 0,
        priority: int = 0,
        budget: int = 0,
        physical: bool = False,
    ):
        self.model = model
        self.ratelimiter = RateLimiter(rate, period)
        self.credentials = credentials or []
        self.init_kwargs = init_kwargs or {}
        self.init_kwargs = {**self.init_kwargs, **self.model.init_kwargs}
        self.priority = priority
        self.budget = budget
        self._model = None
        self.physical = physical
        self.forward = (
            self.model.is_local
            and not self.physical
            and (self.model.load_method == "tf" or self.model.load_method is None)
        )

    async def load(self):
        if self.model.is_local:
            if self.physical:
                from vmc.serve.models import modules

                self._model = getattr(modules, self.model.model_class)(
                    **{**self.init_kwargs, "config": self.model}
                )
            else:
                from vmc.proxy.utils import load_local_model

                self._model = await load_local_model(self.model)
        else:
            self._model = getattr(api_module, self.model.model_class)(
                **{"credentials": self.credentials, **self.init_kwargs, "config": self.model}
            )

    async def alive(self):
        if isinstance(self._model, VMC):
            return await self._model.health()
        return self._model is not None

    async def offload(self):
        if not await self.alive():
            return
        if self.physical:
            del self._model
            from vmc.utils.gpu import torch_gc

            torch_gc()
        else:
            self._model = None

    def __getattr__(self, name):
        async def wrapper(*args, **kwargs):
            if not await self.alive():
                await self.load()
            if not self.ratelimiter():
                await asyncio.sleep(self.ratelimiter.next_available_wait_time)
            return await getattr(self._model, name)(*args, **kwargs)

        return wrapper


class VirtualModel:
    def __init__(self, models: list[ProxyModel], algorithm: Algorithm = Algorithm.ROUND_ROBIN):
        self.models = models
        self.algorithm = algorithm
        self.index = 0

    def choose(self):
        if self.algorithm == Algorithm.RANDOM:
            return random.choice(self.models)
        if self.algorithm == Algorithm.ROUND_ROBIN:
            return self.models[self.index]
        if self.algorithm == Algorithm.LEAST_BUSY:
            return min(self.models, key=lambda m: m.ratelimiter._count)
        if self.algorithm == Algorithm.PRIORITY:
            return max(self.models, key=lambda m: m.priority)
        if self.algorithm == Algorithm.BUDGET:
            return max(self.models, key=lambda m: m.budget)

    def __getattr__(self, name):
        model = self.choose()
        return getattr(model, name)
