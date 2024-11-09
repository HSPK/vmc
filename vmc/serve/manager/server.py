import asyncio
import os
from contextlib import asynccontextmanager

import psutil
from fastapi import FastAPI
from loguru import logger
from typing_extensions import TypedDict

from vmc.serve import SERVER_FAILED_MSG, SERVER_STARTED_MSG
from vmc.types._base import BaseOutput
from vmc.types.errors.status_code import HTTP_CODE, VMC_CODE
from vmc.types.serve.serve import ListServerInfo, ListServerResponse, ServeResponse

from .params import ServeParams, StopParams


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
            return BaseOutput(
                status_code=HTTP_CODE.MODEL_LOAD_ERROR,
                code=VMC_CODE.MODEL_LOAD_ERROR,
                msg="No free GPUs available",
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
        return ServeResponse(
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
            with open(f"logs/{params['name']}.log", "r") as f:
                msg = f.read()
            return BaseOutput(
                status_code=HTTP_CODE.MODEL_LOAD_ERROR, code=VMC_CODE.MODEL_LOAD_ERROR, msg=msg
            ).to_response()
    except Exception as e:
        logger.exception(e)
        return BaseOutput(
            status_code=HTTP_CODE.MODEL_LOAD_ERROR, code=VMC_CODE.MODEL_LOAD_ERROR, msg=str(e)
        ).to_response()
    started_processes[params["name"]] = {
        "process": process,
        "params": params,
        "pid": process.pid,
    }
    return ServeResponse(port=params["port"], pid=process.pid)


@app.post("/stop")
async def stop(params: StopParams):
    name = params["name"]
    if name not in started_processes:
        return BaseOutput(
            status_code=HTTP_CODE.MODEL_STOP_ERROR, code=VMC_CODE.MODEL_STOP_ERROR
        ).to_response()
    p = started_processes.pop(name)["process"]
    logger.debug(f"Killing model {name} with pid {p.pid}")
    killpg(p.pid)
    logger.debug(f"Model {name} stopped")
    return BaseOutput()


@app.get("/list")
async def list_servers():
    return ListServerResponse(
        servers={
            k: ListServerInfo(params=v["params"], pid=v["pid"])
            for k, v in started_processes.items()
        }
    )


@app.get("/health")
async def health():
    return BaseOutput(msg="OK")
