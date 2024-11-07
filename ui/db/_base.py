from abc import ABC, abstractmethod
from functools import cached_property

from loguru import logger

from .schema import ChatMessage, Conversation, ConvSummary


class LazyDBProxy:
    def __init__(self, db_cls: type["DB"], *args, **kwargs):
        self.db_cls = db_cls
        self.args = args
        self.kwargs = kwargs

    @cached_property
    def db(self):
        return self.db_cls(*self.args, **self.kwargs)

    def __getattr__(self, name):
        def lazy_func(*args, **kwargs):
            try:
                ret = getattr(self.db, name)(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error calling {name}: {e}")
            return ret

        return lazy_func


class DB(ABC):
    @abstractmethod
    def get_conv(conv_id: str) -> Conversation:
        pass

    @abstractmethod
    def new_conv(user_id: str, msg: ChatMessage | None = None) -> str:
        pass

    @abstractmethod
    def delete_conv(conv_id: str) -> None:
        pass

    @abstractmethod
    def rename_conv(conv_id: str, title: str) -> None:
        pass

    @abstractmethod
    def conversations(user_id: str) -> list[ConvSummary]:
        pass

    @abstractmethod
    def examples() -> list[str]:
        pass

    @abstractmethod
    def get_message(conv_id: str, msg_id: str) -> ChatMessage:
        pass

    @abstractmethod
    def append_message(conv_id: str, msg: ChatMessage) -> None:
        pass

    @abstractmethod
    def save_state(message_id: str, state: dict) -> None:
        pass

    @abstractmethod
    def save_log(message_id: str, log: str) -> None:
        pass

    @abstractmethod
    def get_state(self, message_id: str):
        pass

    @abstractmethod
    def get_log(self, message_id: str):
        pass

    @abstractmethod
    async def upvote(self, conv_id: str, message_id: str):
        pass

    @abstractmethod
    async def downvote(self, conv_id: str, message_id: str):
        pass
