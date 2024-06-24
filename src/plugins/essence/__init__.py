import random
import sqlite3

import nonebot
from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.rule import is_type

config = nonebot.get_driver().config
db = sqlite3.connect("essence.db")
db.execute(
    "CREATE TABLE IF NOT EXISTS essences (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT)"
)
db.commit()


async def rule_group(event: GroupMessageEvent) -> bool:
    return event.group_id in config.groups


async def rule_admin(event: GroupMessageEvent) -> bool:
    return event.user_id in config.admins


cmd_add = on_command("设精", is_type(GroupMessageEvent) & rule_group)


@cmd_add.handle()
async def fn_add(event: GroupMessageEvent):
    reply = event.reply

    if reply is None:
        return

    content = reply.message.extract_plain_text()
    db.execute("INSERT INTO essences (content) VALUES (?)", (content,))
    db.commit()
    await cmd_add.send("设精成功！")


cmd_clear = on_command("清空设精", is_type(GroupMessageEvent) & rule_group & rule_admin)


@cmd_clear.handle()
async def fn_clear():
    db.execute("DELETE FROM essences")
    db.commit()
    await cmd_clear.send("清空设精成功！")


cmd_show = on_command("爆典", is_type(GroupMessageEvent) & rule_group)


@cmd_show.handle()
async def fn_show():
    cursor = db.cursor()
    cursor.execute("SELECT content FROM essences")
    contents = cursor.fetchall()
    cursor.close()

    if not contents:
        return

    content = random.choice(contents)[0]
    await cmd_show.send(content)
