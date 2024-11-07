import os

from motor.motor_asyncio import AsyncIOMotorClient

from ui.db._base import DB
from ui.db.schema import ChatMessage, Conversation, ConvSummary
from ui.db.utils import iso_datetime


class MongoDB(DB):
    def __init__(self, mongo_uri: str | None = None, db_name: str = "fop"):
        super().__init__()
        if mongo_uri is None:
            mongo_uri = os.getenv("MONGO_URI")
        assert mongo_uri, "MONGO_URI is not set"
        self.mongo_uri = mongo_uri
        self.client = AsyncIOMotorClient(mongo_uri)
        self.db = self.client[db_name]

    async def _init(self):
        if "conversations" not in self.db.list_collection_names():
            self.db.create_collection("conversations")
            # Create index
            await self.db.conversations.create_index("user_id")
            await self.db.conversations.create_index("messages.id")

    async def get_conv(self, user_id: str, conv_id: str) -> Conversation:
        collection = self.db.get_collection("conversations")
        ret = await collection.find_one({"id": conv_id}, projection={"_id": False})
        assert ret, f"Conversation {conv_id} not found"
        conv = Conversation.model_validate(ret)
        assert conv.user_id == user_id, "Conversation User ID does not match"
        return conv

    async def new_conv(self, user_id: str, msg: ChatMessage | None = None) -> str:
        conv = Conversation(user_id=user_id, title="New Conversation", messages=[])
        msg.conv_id = conv.id
        if msg:
            conv.messages.append(msg)
        await self.db.conversations.insert_one(conv.model_dump())
        return conv.id

    async def conversations(self, user_id: str) -> list[ConvSummary]:
        collection = self.db.get_collection("conversations")
        projection = {
            "_id": False,
            "id": 1,
            "user_id": 1,
            "create_time": 1,
            "update_time": 1,
            "title": 1,
            "messages": {"$slice": -1},
        }
        _sort = [("update_time", -1)]
        cursor = collection.find({"user_id": user_id}, projection=projection, sort=_sort)
        convs = await cursor.to_list()
        if not convs:
            return []
        return [Conversation.model_validate(conv).summary() for conv in convs]

    async def examples(self) -> list[str]:
        return [
            "不同department当前被hold的LOT的wafer的数量总和，根据被wafer数量排序",
            "不同department当前被hold的LOT的数量总和，根据LOT数量排序",
        ]

    async def get_message(self, conv_id: str, msg_id: str):
        ret = await self.db.conversations.find_one(
            {"id": conv_id},
            projection={"messages": {"$elemMatch": {"id": msg_id}}},
        )
        assert ret is not None, "Message not found"
        return ChatMessage.model_validate(ret["messages"][0])

    async def append_message(self, conv_id: str, msg: ChatMessage):
        await self.db.conversations.update_one(
            {"id": conv_id},
            {"$push": {"messages": msg.model_dump()}, "$set": {"update_time": msg.update_time}},
        )

    async def rename_conv(self, conv_id: str, title: str):
        await self.db.conversations.update_one(
            {"id": conv_id}, {"$set": {"title": title, "update_time": iso_datetime()}}
        )

    async def delete_conv(self, conv_id: str):
        await self.db.conversations.delete_one({"id": conv_id})

    async def save_state(self, message_id: str, state: dict):
        await self.db.message_state.insert_one({"id": message_id, "state": state})

    async def save_log(self, message_id: str, log: str):
        await self.db.message_log.insert_one({"id": message_id, "log": log})

    async def get_log(self, message_id: str):
        ret = await self.db.message_log.find_one({"id": message_id})
        return ret["log"] if ret else ""

    async def get_state(self, message_id: str):
        ret = await self.db.message_state.find_one({"id": message_id})
        return ret["state"] if ret else {}

    async def upvote(self, conv_id: str, message_id: str):
        await self.db.conversations.update_one(
            {"id": conv_id, "messages.id": message_id},
            {"$set": {"messages.$.feedback.upvote": True, "messages.$.feedback.downvote": False}},
        )

    async def downvote(self, conv_id: str, message_id: str):
        await self.db.conversations.update_one(
            {"id": conv_id, "messages.id": message_id},
            {"$set": {"messages.$.feedback.downvote": True, "messages.$.feedback.upvote": False}},
        )
