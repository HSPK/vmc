import os

from vmc.proxy import init_vmm
from vmc.proxy.manager import ValidationResult, VirtualModelManager, uniform, validate_models
from vmc.types.errors import ModelNotFoundError
from vmc.types.model_config import ModelConfig, Providers
from vmc.utils import find_available_port


async def init_vmm_from_config(name: str, model_id: str, model_type: str):
    assert model_id == name, "model_id is not required for config method"
    providers = Providers.from_yaml(None).providers
    validated_config = validate_models(providers)
    if model_type is None:
        _id_candidates = [
            uniform(f"{t}/{name}") for t in ["chat", "embedding", "reranker", "audio"]
        ]
    else:
        _id_candidates = [uniform(f"{model_type}/{name}")]
    for _id in _id_candidates:
        if _id in validated_config:
            break
    else:
        raise ModelNotFoundError(msg=f"{name} not found")
    validated_config = {_id: validated_config[_id]}
    vmm = VirtualModelManager(validated_config)
    await vmm.load(_id, physical=True)
    return vmm


async def init_vmm_from_transformers(
    name: str,
    model_id: str,
    model_type: str,
    backend: str,
    device_map_auto: bool,
):
    model_class = {
        "chat": "TransformerGeneration",
        "embedding": "TransformerEmbedding",
        "reranker": "TransformerReranker",
    }[model_type]
    init_kwargs = {"model_id": model_id}
    if model_type == "embedding":
        init_kwargs["backend"] = backend
    if model_type == "chat":
        init_kwargs["device_map"] = "auto" if device_map_auto else None
    model_config = ModelConfig(
        name=name,
        model_class=model_class,
        init_kwargs=init_kwargs,
        type=type,
        is_local=True,
    )
    validated_config: dict[str, ValidationResult] = {
        uniform(f"{type}/{name}"): {
            "config": model_config,
            "credentials": [],
            "common_init_kwargs": {},
        }
    }
    obj = VirtualModelManager(validated_config)
    await obj.load(f"{type}/{name}", physical=True)
    return obj


async def init_vmm_from_tei(
    name: str,
    model_id: str,
    hf_cache_dir: str,
    hf_token_dir: str,
):
    assert hf_token_dir, "hf_token_dir is required"
    port = find_available_port()
    command = [
        "docker",
        "run",
        "--rm",
        "--gpus",
        "all",
        "-v",
        f"{hf_cache_dir}:/data",
        "-v",
        f"{hf_token_dir}:/root/.cache/huggingface",
        "-p",
        f"127.0.0.1:{port}:8000",
        "--pull",
        "always",
        "--name",
        f"tei-{name}",
        "ghcr.io/huggingface/text-embeddings-inference:1.5",
        "--model_id",
        model_id,
    ]
    import subprocess

    pipe = subprocess.Popen(command)
    pipe.wait()
    model_config = ModelConfig(name=name, model_class="TeiEmbedding", init_kwargs={"port": port})
    validated_config: dict[str, ValidationResult] = {
        uniform(f"embedding/{name}"): {
            "config": model_config,
            "credentials": [],
            "common_init_kwargs": {},
        }
    }
    obj = VirtualModelManager(validated_config)
    await obj.load(f"embedding/{name}")
    return obj


init_method_map = {
    "config": init_vmm_from_config,
    "tf": init_vmm_from_transformers,
    "tei": init_vmm_from_tei,
}


async def init_serve_vmm():
    import inspect

    init_args = {
        "name": os.getenv("SERVE_NAME"),
        "model_id": os.getenv("SERVE_MODEL_ID"),
        "model_type": os.getenv("SERVE_TYPE"),
        "backend": os.getenv("SERVE_BACKEND", "torch"),
        "method": os.getenv("SERVE_METHOD", "config"),
        "device_map_auto": os.getenv("SERVE_DEVICE_MAP_AUTO", "False").lower() == "true",
        "hf_cache_dir": os.getenv("VMC_HF_CACHE_DIR"),
        "hf_token_dir": os.getenv("VMC_HF_TOKEN_DIR"),
    }
    assert init_args["name"], "SERVE_NAME is not set"

    if not init_args["model_id"]:
        init_args["model_id"] = init_args["name"]
    init_method = init_method_map.get(init_args["method"])
    if not init_method:
        raise ValueError(f"Invalid method: {init_args['method']}")
    required_args = list(inspect.signature(init_method).parameters.keys())
    args = {k: v for k, v in init_args.items() if k in required_args}
    assert len(args) == len(required_args), f"Missing required arguments: {required_args}"
    init_vmm(await init_method(**args))
