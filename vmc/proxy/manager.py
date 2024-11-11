from typing_extensions import Literal, TypedDict

import vmc.models as api_module
import vmc.serve.models as serve_module
from vmc.models import ModelType
from vmc.types.errors import GroupExistsError, GroupNotFoundError, ModelNotFoundError
from vmc.types.model_config import ModelConfig, ProviderConfig, Providers

from .model import ProxyModel, VirtualModel


def uniform(id: str):
    return id.lower().replace("-", "").strip()


class ValidationResult(TypedDict):
    config: ModelConfig
    credentials: list[dict]
    common_init_kwargs: dict


def validate_models(providers: list[ProviderConfig]):
    result: dict[str, ValidationResult] = {}
    for provider_config in providers:
        for model_config in provider_config.models:
            id_ = uniform(f"{model_config.type}/{model_config.name}")
            if id_ in result:
                id_ = f"{provider_config.provider_name}/{id_}"
                if id_ in result:
                    raise ValueError(f"model {id_} already exists")
            if model_config.is_local and model_config.model_class not in serve_module.model_names:
                raise ValueError(f"{model_config.model_class} not found in local models")
            if not model_config.is_local and model_config.model_class not in api_module.model_names:
                raise ValueError(f"{model_config.model_class} not found in API models")
            result[id_] = {
                "config": model_config,
                "credentials": provider_config.credentials,
                "common_init_kwargs": provider_config.common_init_kwargs,
            }
    return result


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

    def __init__(self, validated_config: dict[str, ValidationResult]):
        self.model_configs = validated_config
        self.loaded_models = {}

    @classmethod
    def from_providers(cls, providers: list[ProviderConfig]):
        validated_config = validate_models(providers)
        return cls(validated_config)

    @classmethod
    def from_yaml(cls, path: str | None):
        validated_config = validate_models(Providers.from_yaml(path).providers)
        return cls(validated_config)

    @property
    def models(self):
        return {m["config"].name: m["config"].dump() for m in self.model_configs.values()}

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
        model = ProxyModel(
            model=self.model_configs[id]["config"],
            credentials=self.model_configs[id]["credentials"],
            init_kwargs=self.model_configs[id]["common_init_kwargs"],
            physical=physical,
        )
        if physical:
            await model.load()
        self.loaded_models[id] = model
        return self.loaded_models[id]

    async def offload(
        self, id: str, type: Literal["chat", "embedding", "audio", "reranker"] | None = None
    ):
        """Offload a virtual model by id."""
        if type is None:
            _id_candidates = [
                uniform(f"{t}/{id}") for t in ["chat", "embedding", "reranker", "audio"]
            ]
        else:
            _id_candidates = [uniform(f"{type}/{id}")]
        for _id in _id_candidates:
            if _id in self.loaded_models:
                break
        else:
            raise ModelNotFoundError(msg=f"{id} not found")
        await self.loaded_models[_id].offload()
        del self.loaded_models[_id]
