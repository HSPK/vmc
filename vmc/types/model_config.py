import os
from typing import Any, Literal

import pydantic

from vmc.types.pricing import Pricing


class BaseModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(protected_namespaces=())


class ModelConfig(BaseModel):
    name: str
    model_class: str
    init_kwargs: dict[str, Any] = {}
    default_params: dict[str, Any] = {}
    type: Literal["chat", "embedding", "audio", "reranker"] = "chat"
    pricing: Pricing | None = None
    context_window: int | None = None
    output_dimension: int | None = None
    max_tokens: int | None = None
    description: str | None = None
    knowledge_date: str | None = None
    port: int | None = None
    gpu_limit: int = 0
    """GPU limit for local model, 0 means no limit"""

    is_local: bool = False

    load_method: Literal["tf", "vllm", "ollama"] | None = None
    """Use to specify the load method for local model"""

    backend: Literal["torch", "onnx", "openvino"] = "torch"
    """Local model backend"""

    device_map_auto: bool = False
    """Local model device map auto"""

    def dump(self):
        d = self.model_dump()
        d.pop("init_kwargs")
        return d

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.max_tokens is None and self.context_window is not None:
            self.max_tokens = self.context_window


class ProviderConfig(BaseModel):
    provider_name: str = "unknown"
    model_page: str = ""
    document_page: str = ""
    credentials: list[dict] | None = None
    models: list[ModelConfig] | None = None
    is_local: bool = False
    common_init_kwargs: dict[str, Any] = {}

    @classmethod
    def from_yaml(cls, path: str):
        import yaml

        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            obj = cls(**yaml.safe_load(f))
            if "local" in obj.provider_name.lower() or obj.is_local:
                obj.is_local = True
                for model in obj.models:
                    model.is_local = True
            return obj


class Providers(BaseModel):
    providers: list[ProviderConfig]
    """模型提供商配置"""

    @classmethod
    def from_yaml(cls, path: str | None):
        import pathlib

        import yaml

        path = path or os.getenv("VMC_PROVIDERS_CONFIG")
        assert path, "providers config is required"
        cache_model_path = os.getenv("VMC_MODEL_CACHE_DIR")

        with open(path, "r", encoding="utf-8") as f:
            providers = yaml.safe_load(f)
            assert isinstance(providers, dict), "providers config should be a dict"
            assert "providers" in providers, "providers key is required"
            providers = providers["providers"]

        for i in range(len(providers)):
            if isinstance(providers[i], str):
                """如果是字符串，表示是一个yaml文件路径，需要加载yaml文件"""
                path = pathlib.Path(path).parent / f"{providers[i]}.yaml"
                if not path.exists():
                    raise FileNotFoundError(f"File not found: {path}")
                provider = ProviderConfig.from_yaml(path.as_posix())
                providers[i] = provider
                if cache_model_path:
                    """将本地模型model_id转换为绝对路径"""
                    for model in provider.models:
                        if model.is_local:
                            model.init_kwargs["model_id"] = os.path.join(
                                cache_model_path,
                                model.init_kwargs["model_id"],
                            )
        return cls(providers=providers)
