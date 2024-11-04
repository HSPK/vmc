import os
import random

from vmc.types.model_config import ModelConfig


class BaseModel:
    """Base model for actual models.
    Functions starting with `_` are meant to be used by the vmc itself."""

    def __init__(
        self,
        config: ModelConfig,
        model_id: str | None = None,
        credentials: list[dict[str, str]] | None = None,
    ):
        """Initialize the model

        Args:
            model_id (str): Model ID, in the form of `domain/model_name`
            config (ModelConfig): Configuration for the model
            credentials (list[dict] | None, optional): Credentials for the model. Usually contains API keys and Hosts.
                If the value is `.env.vmc/xxx`, it will be replaced with the actual value from the environment variable.. Defaults to None.
            callbacks (list[Callback], optional): Callbacks. Defaults to [].
        """
        self.config = config
        self.model_id = model_id or config.name
        self.pricing = config.pricing
        self.credentials = credentials

    def _choose_credential(self):
        if self.credentials:
            return random.choice(self.credentials)
        return None

    def set_credential(self):
        if self.credentials:
            credential = self._choose_credential()
            ret = {}
            for k, v in credential.items():
                if v.startswith(".env.vmc/"):
                    os.environ[k] = os.getenv(v[9:])
                else:
                    ret[k] = v
            self.validate_credential(ret)
            return ret
        return {}

    def validate_credential(self, credential: dict[str, str]):
        return True
