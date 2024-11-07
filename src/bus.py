from nonebot import get_bot
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageSegment


async def send(
    event: GroupMessageEvent,
    message: str | Message | MessageSegment,
    reply: bool = False,
):
    msg = (
        Message(MessageSegment.reply(event.message_id)) + message
        if reply
        else Message(message)
    )

    await get_bot().send(event, msg)
