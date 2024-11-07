from ui.db._base import LazyDBProxy
from ui.db.backends.mongodb import MongoDB
from ui.db.schema import BotMessage, UserMessage

backend: MongoDB = LazyDBProxy(MongoDB)

bot_avatar = "https://robohash.org/1?bgset=bg2"

get_conv = backend.get_conv
conversations = backend.conversations
examples = backend.examples
append_message = backend.append_message
rename_conv = backend.rename_conv
delete_conv = backend.delete_conv
save_state = backend.save_state
save_log = backend.save_log
get_log = backend.get_log
get_state = backend.get_state
upvote = backend.upvote
downvote = backend.downvote

databases = []
database_descs = []


async def new_conv(user_id: str, user_message: str | None = None) -> str:
    if user_message:
        msg = UserMessage(text=user_message)
    else:
        msg = BotMessage(text="Hello! How can I help you?", avatar=bot_avatar)
    return await backend.new_conv(user_id, msg)
