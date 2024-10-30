import asyncio
import os
from contextlib import asynccontextmanager

import psutil
from fastapi import FastAPI
from loguru import logger
from typing_extensions import TypedDict

from vmc.serve import SERVER_FAILED_MSG, SERVER_STARTED_MSG

from .params import BaseResponse, ServeParams, StatusCode, StopParams


class ProcessInfo(TypedDict):
    process: asyncio.subprocess.Process
    params: ServeParams
    pid: int


started_processes: dict[str, ProcessInfo] = {}


def killpg(pid):
    try:
        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            child.kill()
        parent.kill()
    except psutil.NoSuchProcess:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    print("Stopping all processes")
    for p in started_processes.values():
        killpg(p["process"].pid)


app = FastAPI(lifespan=lifespan)


@app.post("/serve")
async def serve(params: ServeParams):
    from vmc.utils import get_freer_gpus

    envs = os.environ.copy()
    if "gpu_limit" in params and params["gpu_limit"] > 0:
        if params["gpu_limit"] > 1:
            params["device_map_auto"] = True
        gpus = get_freer_gpus(params["gpu_limit"])
        if not gpus:
            return BaseResponse(
                code=StatusCode.SERVE_ERROR, msg="No free GPUs available"
            ).to_response()
        envs["CUDA_VISIBLE_DEVICES"] = ",".join(map(str, gpus))
    command = [
        "vmc",
        "serve",
        params["name"],
    ]
    options = [
        "model_id",
        "method",
        "type",
        "host",
        "port",
        "api_key",
        "backend",
    ]
    for option in options:
        if option in params and params[option]:
            command += [f"--{option.replace('_', '-')}", str(params[option])]
    if "device_map_auto" in params and params["device_map_auto"]:
        command += ["--device-map-auto"]
    if params["name"] in started_processes:
        return BaseResponse(
            port=started_processes[params["name"]]["params"]["port"],
            pid=started_processes[params["name"]]["process"].pid,
        )
    try:
        logger.debug(f"Starting model {params['name']} with command: {' '.join(command)}")
        os.makedirs("logs", exist_ok=True)
        with open(f"logs/{params['name']}.log", "w") as f:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=f,
                env=envs,
            )
    except Exception as e:
        logger.error(f"Failed to create process: {e}")
        return BaseResponse(code=StatusCode.SERVE_ERROR, msg=str(e)).to_response()
    try:
        load_success = False
        output = ""
        while True:
            output = await process.stdout.readline()
            if output:
                print(output.decode().strip())
            if process.returncode is not None:
                break
            if SERVER_STARTED_MSG in output.decode():
                load_success = True
                break
            if SERVER_FAILED_MSG in output.decode():
                break

            await asyncio.sleep(0.5)
        if not load_success:
            logger.error(f"Failed to load model: {output}")
            return BaseResponse(
                code=StatusCode.SERVE_ERROR, msg=f"Failed to load model: {output.decode()}"
            ).to_response()
    except Exception as e:
        logger.exception(e)
        return BaseResponse(code=StatusCode.SERVE_ERROR, msg=str(e)).to_response()
    started_processes[params["name"]] = {
        "process": process,
        "params": params,
        "pid": process.pid,
    }
    return BaseResponse(
        port=params["port"],
        pid=process.pid,
    )


@app.post("/stop")
async def stop(params: StopParams):
    name = params["name"]
    if name not in started_processes:
        return BaseResponse(code=StatusCode.STOP_ERROR, msg=f"Model {name} not found")
    p = started_processes.pop(name)["process"]
    logger.debug(f"Killing model {name} with pid {p.pid}")
    killpg(p.pid)
    logger.debug(f"Model {name} stopped")
    return BaseResponse()


@app.get("/list")
async def list_servers():
    return {k: {"params": v["params"], "pid": v["pid"]} for k, v in started_processes.items()}


@app.get("/health")
async def health():
    return BaseResponse()
