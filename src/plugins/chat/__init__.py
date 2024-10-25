from time import time

from nonebot import get_driver, on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message
from nonebot.params import CommandArg
from nonebot.rule import is_type
from openai import OpenAI

config = get_driver().config
avail_chat = 0
chat_client = OpenAI(
    api_key=config.api_key,
    base_url=config.base_url,
)


def request_chat(prompt: str) -> str:
    return (
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


cmd_chat = on_command("聊天", is_type(GroupMessageEvent), force_whitespace=True)


@cmd_chat.handle()
async def fn_chat(args: Message = CommandArg()):
    global avail_chat
    now = time()

    if now < avail_chat:
        await cmd_chat.send("别急！")
        return

    prompt = args.extract_plain_text().strip()

    if len(prompt) < 4:
        await cmd_chat.send("太短！")
        return

    avail_chat = now + 10
    await cmd_chat.send(request_chat(prompt))
