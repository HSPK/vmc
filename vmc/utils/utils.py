import hashlib
import subprocess

import numpy as np


def get_gpu_free_memory():
    cmd = "nvidia-smi --query-gpu=memory.free --format=csv,nounits,noheader"
    output = subprocess.check_output(cmd, shell=True).decode("utf-8")
    memory = [int(x) for x in output.strip().split("\n")]
    return memory


def get_freer_gpu(top_k=1, exclude_gpus=[]):
    gpu_memory = get_gpu_free_memory()
    for i in exclude_gpus:
        gpu_memory[i] = -1
    return sorted(np.argsort(gpu_memory)[::-1][:top_k])


def torch_gc():
    import gc

    import torch

    if torch.cuda.is_available():
        gc.collect()
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()


def hash_password(password: str):
    """
    Hash a password"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def find_available_port():
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port
