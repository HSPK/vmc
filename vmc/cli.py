import os
import subprocess

import click
from dotenv import find_dotenv, load_dotenv
from typing_extensions import Literal

load_dotenv(find_dotenv())


@click.group()
@click.version_option()
def cli():
    pass


@cli.command(name="serve")
@click.argument("name")
@click.option("--model-id", default=None)
@click.option("--method", default="config")
@click.option("--type", default=None)
@click.option("--host", default="localhost")
@click.option("--port", default=8100)
@click.option("--api-key", default=None)
@click.option("--reload", is_flag=True)
@click.option("--backend", default="torch")
@click.option("--device-map-auto", is_flag=True)
def serve(
    name: str,
    model_id: str,
    method: Literal["config", "tf", "vllm", "ollama"],
    type: Literal["chat", "embedding", "audio", "reranker"],
    backend: Literal["torch", "onnx", "openvino"],
    host: str,
    port: int,
    api_key: str,
    reload: bool,
    device_map_auto: bool,
):
    from vmc.serve import SERVER_FAILED_MSG

    if model_id is None:
        model_id = name

    os.environ["SERVE_NAME"] = name
    os.environ["SERVE_MODEL_ID"] = model_id
    os.environ["SERVE_METHOD"] = method
    if type:
        os.environ["SERVE_TYPE"] = type
    os.environ["SERVE_BACKEND"] = backend
    os.environ["SERVE_DEVICE_MAP_AUTO"] = str(device_map_auto)

    if api_key:
        os.environ["SERVE_API_KEY"] = api_key
    if reload:
        cmd = [
            "uvicorn",
            "vmc.serve.server:create_app",
            "--reload",
            "--host",
            host,
            "--port",
            str(port),
        ]
    else:
        cmd = [
            "gunicorn",
            "-b",
            f"{host}:{port}",
            "-k",
            "uvicorn.workers.UvicornWorker",
            "--log-level",
            "info",
            "--timeout",
            "300",
            # "--factory",
            "vmc.serve.server:create_app",
        ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"{SERVER_FAILED_MSG} {str(e)}")
        exit(1)


def get_last_commit_message():
    import subprocess

    try:
        return subprocess.check_output(
            ["git", "log", "-1", "--pretty=%B"], universal_newlines=True
        ).strip()
    except subprocess.CalledProcessError:
        return "Unknown"


def get_version():
    import importlib.metadata

    return importlib.metadata.version("vmc")


@cli.command()
@click.option("--port", "-p", default=8080)
def dashboard(port: int):
    pass


@cli.command(name="start")
@click.option("--port", "-p", default=None)
@click.option("--reload", is_flag=True)
def start_server(port: int | None = None, reload: bool = False):
    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv())
    workers = os.getenv("VMC_WORKERS", 1)
    host = os.getenv("VMC_SERVER_HOST", "localhost")
    port = port or os.getenv("VMC_SERVER_PORT", 8000)
    title = f"VMC {get_version()} started"
    msg = get_last_commit_message()
    from rich import print

    print(f"[bold green]{title}[/bold green]\n{msg}")
    if not reload:
        cmd = [
            "gunicorn",
            "-w",
            str(workers),
            "-b",
            f"{host}:{port}",
            "--worker-class",
            "uvicorn.workers.UvicornWorker",
            "--timeout",
            "300",
            "--log-level",
            "info",
            "vmc.proxy_server:app",
        ]
    else:
        cmd = [
            "uvicorn",
            "vmc.proxy_server:app",
            "--reload",
            "--host",
            host,
            "--port",
            str(port),
        ]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(e)
        exit(1)


@cli.command()
@click.option("--host", default="localhost")
@click.option("--port", default=8200)
@click.option("--reload", is_flag=True)
def manager(host: str, port: int, reload: bool):
    import subprocess

    if not reload:
        command = [
            "gunicorn",
            "-b",
            f"{host}:{port}",
            "-k",
            "uvicorn.workers.UvicornWorker",
            "--log-level",
            "info",
            "--timeout",
            "300",
            "vmc.serve.manager.server:app",
        ]
    else:
        command = [
            "uvicorn",
            "vmc.serve.manager.server:app",
            "--host",
            host,
            "--port",
            str(port),
            "--reload",
        ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(e)
        exit(1)


if __name__ == "__main__":
    cli()
