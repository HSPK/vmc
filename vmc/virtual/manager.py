from typing_extensions import Literal

import vmc.models as api_module
import vmc.models.local as local_module
from vmc.models import ModelType
from vmc.types.errors import GroupExistsError, GroupNotFoundError, ModelNotFoundError
from vmc.types.model_config import ModelConfig, ProviderConfig, Providers

from .model import PhysicalModel, VirtualModel


def uniform(id: str):
    return id.lower().replace("-", "").strip()


def validate_models(providers: list[ProviderConfig]):
    model_configs: dict[str, ModelConfig] = {}
    credentials: dict[str, list[dict]] = {}
    for p in providers:
        for m in p.models:
            id_ = uniform(f"{m.type}/{m.name}")
            if id_ in model_configs:
                id_ = f"{p.provider_name}/{id_}"
                if id_ in model_configs:
                    raise ValueError(f"model {id_} already exists")
            if m.is_local and not hasattr(local_module, m.model_class):
                raise ValueError(f"{m.model_class} not found in local models")
            if not m.is_local and not hasattr(api_module, m.model_class):
                raise ValueError(f"{m.model_class} not found in API models")
            model_configs[id_] = m
            credentials[id_] = p.credentials
    return model_configs, credentials


class VirtualModelManager:
    """Manage virtual deep learning models.
    Concept: request a model by id, virtual model will return the model instance.
    If the model is not loaded or not alive, virtual model will reload the model.
    If the model is basy, virtual model will use schedule algorithm to find a proper model.

    Support Custom Model Group. All models in the same group will be treated as a single model.
    VirtualModel will use schedule algorithm to find a proper model in the group.

    Support Model Priority. VirtualModel will use priority to find a proper model.
    Supported Algorithms: Random, Round Robin, Least Busy, Priority, Budget, etc.
    """

    model_configs: dict[str, ModelConfig]
    credentials: dict[str, list[dict]]

    def __init__(self, model_configs: dict[str, ModelConfig], credentials: dict[str, list[dict]]):
        self.model_configs, self.credentials = model_configs, credentials
        self.loaded_models = {}

    @classmethod
    def from_providers(cls, providers: list[ProviderConfig]):
        model_configs, credentials = validate_models(providers)
        return cls(model_configs, credentials)

    @classmethod
    def from_yaml(cls, path: str | None):
        providers = Providers.from_yaml(path).providers
        model_configs, credentials = validate_models(providers)
        return cls(model_configs, credentials)

    @classmethod
    async def from_serve(
        cls,
        name: str,
        model_id: str | None = None,
        method: Literal["config", "tf", "ollama", "vllm"] = "config",
        type: Literal["chat", "embedding", "audio", "reranker"] = "chat",
        backend: Literal["torch", "onnx", "openvino"] = "torch",
        device_map_auto: bool = False,
    ):
        model_id = model_id or name
        if method == "config":
            assert model_id == name, "model_id is not required for config method"
            providers = Providers.from_yaml(None).providers
            model_configs, credentials = validate_models(providers)
            _id = uniform(f"{type}/{name}")
            if _id not in model_configs:
                raise ModelNotFoundError(msg=f"{_id} not found")
            model_configs = {_id: model_configs[_id]}
            credentials = {_id: credentials[_id]}
            obj = cls(model_configs, credentials)
            await obj.load(_id, physical=True)
            return obj
        elif method == "tf":
            assert type != "audio", "audio model is not supported"
            model_class = {
                "chat": "TransformerGeneration",
                "embedding": "TransformerEmbedding",
                "reranker": "TransformerReranker",
            }[type]
            init_kwargs = {"model_id": model_id}
            if type == "embedding":
                init_kwargs["backend"] = backend
            if type == "chat":
                init_kwargs["device_map"] = "auto" if device_map_auto else None
            model_config = ModelConfig(
                name=name,
                model_class=model_class,
                init_kwargs=init_kwargs,
                type=type,
                is_local=True,
            )
            model_configs = {uniform(f"{type}/{name}"): model_config}
            credentials = {uniform(f"{type}/{name}"): []}
            obj = cls(model_configs, credentials)
            await obj.load(f"{type}/{name}", physical=True)
            return obj
        else:
            raise ValueError(f"method {method} not supported")

    @property
    def models(self):
        return {m.name: m.dump() for m in self.model_configs.values()}

    async def add_model_group(
        self, group_name: str, model_ids: list[str], algorithm: str = "round_robin"
    ):
        """Add a model group with model ids and algorithm.

        Args:
            group_name: str, the group name.
            model_ids: list[str], the model ids in the group.
            algorithm: str, the algorithm to select model in the group.
        """
        if group_name in self.loaded_models:
            raise GroupExistsError(msg=f"group {group_name} already exists")
        for model_id in model_ids:
            if model_id not in self.model_configs:
                raise ModelNotFoundError(msg=f"{model_id} not found")
            self.load(model_id)
        self.loaded_models[group_name] = VirtualModel(
            models=[self.loaded_models[id] for id in model_ids]
        )

    async def remove_model_group(self, group_name: str):
        """Remove a model group.

        Args:
            group_name: str, the group name.
        """
        if group_name not in self.loaded_models:
            raise GroupNotFoundError(msg=f"group {group_name} not found")
        del self.loaded_models[group_name]

    async def get(
        self, id: str, type: Literal["chat", "embedding", "audio", "reranker"] = "chat"
    ) -> ModelType:
        return await self.load(f"{type}/{id}")

    async def load(self, id: str, physical: bool = False):
        """Load a virtual model by id."""
        id = uniform(id)
        if id in self.loaded_models:
            return self.loaded_models[id]
        if id not in self.model_configs:
            raise ModelNotFoundError(msg=f"{id} not found") from None
        model = PhysicalModel(
            model=self.model_configs[id],
            credentials=self.credentials[id],
            physical=physical,
        )
        if physical:
            await model.load()
        self.loaded_models[id] = model
        return self.loaded_models[id]

    async def offload(self, id: str, type: Literal["chat", "embedding", "audio", "reranker"]):
        """Offload a virtual model by id."""
        id = uniform(f"{type}/{id}")
        if id not in self.loaded_models:
            raise ModelNotFoundError(msg=f"{id} not found")
        await self.loaded_models[id].offload()
        del self.loaded_models[id]
