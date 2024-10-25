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
                    "content": "你是一个基于大语言模型的聊天群机器人助手，你在回复时会始终避免使用不利于人类阅读的元素，例如 **加粗文本** 或者 ```代码块```\n你不会回复涉及中华人民共和国政治敏感内容，或者涉及色情、赌博、毒品、暴力、恐怖主义等违法违规内容",
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
