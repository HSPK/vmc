import os

import requests
from loguru import logger

from vmc.types.errors import errors as err

serve_host = os.getenv("VMC_SERVE_HOST", "localhost")
serve_port = os.getenv("VMC_SERVE_PORT", "9000")
serve_url = f"http://{serve_host}:{serve_port}"


def is_manager_started():
    url = f"{serve_url}/ping"
    try:
        ret = requests.get(url)
        assert ret.json()["msg"] == "success"
    except Exception as e:
        logger.error(f"{url} is not started: {e}, {ret.text}")
        return False
    return True


def serve_model(
    id: str,
    config_path: str,
    gpu_limit: int = 1,
    exclude_gpus: list[int] = [],
):
    if not is_manager_started():
        logger.error("Manager is not started")
        raise err.ManagerNotLoadedError()
    try:
        ret = requests.post(
            f"{serve_url}/start-server",
            json={"id": id, "config_path": config_path, "gpu_limit": gpu_limit},
        )
    except Exception as e:
        msg = f"Failed to start local server: {e}"
        logger.error(msg)
        raise Exception(msg) from e
    if ret.status_code != 200:
        msg = f"Failed to start local server: {ret.json()}"
        logger.error(msg)
        raise Exception(msg)
    return ret.json()["port"]


def stop_local_server(id: str | None = None):
    if not is_manager_started():
        logger.error("Manager is not started")
        return False
    try:
        ret = requests.post(f"{serve_url}/stop-server", json={"id": id})
    except Exception as e:
        logger.error(f"Failed to stop local server: {e}")
        return False
    if ret.status_code != 200:
        logger.error(f"Failed to stop local server: {ret.json()}")
        return False
    return True


def list_local_models():
    pass


def get_pids_by_ports(ports: list[int]):
    pids = {}
    for port in ports:
        ret = os.popen(f"lsof -t -i:{port}").read()
        pids[port] = [int(x) for x in ret.split("\n") if x]
    return pids


def get_gpu_memory_by_ports(ports: list[int]):
    pids = get_pids_by_ports(ports)
    memory_info = os.popen(
        "nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader,nounits"
    ).read()
    memory_info = {int(x.split(",")[0]): int(x.split(",")[1]) for x in memory_info.split("\n") if x}
    memory_usage = {}
    for port in ports:
        memory_usage[port] = sum([memory_info.get(pid, 0) for pid in pids.get(port, [])])
    return memory_usage


def get_overall_gpu_usage():
    info = os.popen(
        "nvidia-smi --query-gpu=name,index,memory.total,memory.used,utilization.gpu --format=csv"
    ).read()
    info = [[x.strip() for x in line.split(",")] for line in info.split("\n") if line]
    header = info[0]
    return [{header[i]: x[i] for i in range(len(header))} for x in info[1:]]


def list_local_servers():
    if not is_manager_started():
        logger.error("Manager is not started")
        return []
    try:
        ret = requests.get(f"{serve_url}/list-servers")
        meomry_usage = get_gpu_memory_by_ports(ret.json().values())
        info = [
            {"name": name, "port": port, "memory_usage": f"{meomry_usage[port]} MiB"}
            for name, port in ret.json().items()
        ]
    except Exception as e:
        logger.error(f"Failed to list local servers: {e}")
        return []
    if ret.status_code != 200:
        logger.error(f"Failed to list local servers: {ret}")
        return []
    return info
