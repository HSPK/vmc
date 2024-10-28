import os

import click
from dotenv import find_dotenv, load_dotenv
from typing_extensions import Literal

load_dotenv(find_dotenv())


@click.group()
@click.version_option()
def cli():
    pass


@cli.group()
def manager():
    pass


@cli.command(name="serve")
@click.argument("name")
@click.option("--model-id", default=None)
@click.option("--method", default="config")
@click.option("--type", default="chat")
@click.option("--host", default="localhost")
@click.option("--port", default=8100)
@click.option("--api-key", default=None)
@click.option("--debug", is_flag=True)
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
    debug: bool,
    device_map_auto: bool,
):
    if model_id is None:
        model_id = name

    os.environ["SERVE_NAME"] = name
    os.environ["SERVE_MODEL_ID"] = model_id
    os.environ["SERVE_METHOD"] = method
    os.environ["SERVE_TYPE"] = type
    os.environ["SERVE_BACKEND"] = backend
    os.environ["SERVE_DEVICE_MAP_AUTO"] = str(device_map_auto)

    if api_key:
        os.environ["SERVE_API_KEY"] = api_key
    if debug:
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
    cmd = " ".join(cmd)
    from rich import print

    print(cmd)

    ret = os.system(cmd)

    if ret != 0:
        print("Failed to start server")


@cli.group()
def dashboard():
    pass


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


@dashboard.command(name="start")
@click.option("--config-path", default=None)
@click.option("--detach", "-d", is_flag=True)
@click.option("--port", "-p", default=8080)
def start_dashboard(config_path: str, detach: bool, port: int):
    import os

    os.system(
        f"gunicorn -b 127.0.0.1:{port} "
        f"-k uvicorn.workers.UvicornWorker "
        f"-e CONFIG_PATH={config_path} "
        f"vmc.dashboard:demo {'-D' if detach else ''}"
    )


@dashboard.command(name="stop")
@click.option("--config-path", default=None)
@click.option("--port", "-p", default=None)
def stop_dashboard(config_path: str | None, port: int | None = None):
    import os

    ret = os.system(f"kill -9 $(lsof -t -i:{port})")
    if ret != 0:
        print("Dashboard not running")
    else:
        print("Dashboard stopped")


@cli.command(name="start")
@click.option("--detach", "-d", is_flag=True)
@click.option("--port", "-p", default=None)
@click.option("--reload", is_flag=True)
def start_server(detach: bool = False, port: int | None = None, reload: bool = False):
    workers = os.getenv("VMC_WORKERS", 1)
    host = os.getenv("VMC_SERVER_HOST", "localhost")
    port = port or os.getenv("VMC_SERVER_PORT", 8000)
    title = f"VMC {get_version()} started"
    msg = get_last_commit_message()
    from rich import print

    print(f"[bold green]{title}[/bold green]\n{msg}")
    if not reload:
        start_cmd = (
            f"gunicorn -w {workers} -b {host}:{port} "
            f"--worker-class uvicorn.workers.UvicornWorker "
            f"--timeout 300 "
            "--log-level info "
            f"vmc.proxy_server:app {'-D' if detach else ''} "
        )
    else:
        start_cmd = f"uvicorn vmc.proxy_server:app --reload --host {host} --port {port}"
    print(start_cmd)
    os.system(start_cmd)


@manager.command(name="start")
@click.option("--config-path", default=None)
@click.option("--detach", "-d", is_flag=True)
@click.option("--host", default="localhost")
@click.option("--port", default=9000)
def start_manager(config_path: str, detach: bool, host: str, port: int):
    import os

    os.system(
        f"gunicorn -b {host}:{port} "
        f"-k uvicorn.workers.UvicornWorker "
        f"vmc.manager.app:app {'-D' if detach else ''}"
    )


if __name__ == "__main__":
    cli()
