from time import time

from nonebot import get_driver, on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message
from nonebot.params import CommandArg
from nonebot.rule import is_type
from openai import OpenAI

from bus import send

AVAIL_CHAT: float = 0

config = get_driver().config
chat_client = OpenAI(
    api_key=config.api_key,
    base_url=config.base_url,
)


def request_chat(prompt: str) -> str:
    response = (
        chat_client.chat.completions.create(
            model=config.model,
            messages=[
                {
                    "role": "system",
                    "content": config.system_prompt,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0,
        )
        .choices[0]
        .message.content
    )

    return response if response is not None else ""


cmd_chat = on_command("聊天", is_type(GroupMessageEvent), force_whitespace=True)


@cmd_chat.handle()
async def fn_chat(event: GroupMessageEvent, args: Message = CommandArg()):
    global AVAIL_CHAT
    now = time()

    if now < AVAIL_CHAT:
        await send(event, "别急！")
        return

    prompt = args.extract_plain_text().strip()

    if len(prompt) < 4:
        await send(event, "太短！")
        return

    AVAIL_CHAT = now + 10
    await send(event, request_chat(prompt))
