import random
import sqlite3

import nonebot
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.rule import is_type

config = nonebot.get_driver().config
db = sqlite3.connect("essence.db")
db.execute(
    "CREATE TABLE IF NOT EXISTS essences (id INTEGER PRIMARY KEY AUTOINCREMENT, qq INTEGER, essence TEXT)"
)
db.execute(
    "CREATE TABLE IF NOT EXISTS aliases (id INTEGER PRIMARY KEY AUTOINCREMENT, qq INTEGER, alias TEXT)"
)
db.commit()


def insert_essence(qq: int, essence: str):
    db.execute("INSERT INTO essences (qq, essence) VALUES (?, ?)", (qq, essence))
    db.commit()


def select_essence(qq: int = 0, essence: str = ""):
    cursor = db.cursor()

    if qq != 0 and essence != "":
        cursor.execute(
            "SELECT * FROM essences WHERE qq = ? AND essence = ?", (qq, essence)
        )
    elif qq != 0 and essence == "":
        cursor.execute("SELECT * FROM essences WHERE qq = ?", (qq,))
    elif qq == 0 and essence != "":
        cursor.execute("SELECT * FROM essences WHERE essence = ?", (essence,))
    else:
        cursor.execute("SELECT * FROM essences")

    data = cursor.fetchall()
    cursor.close()
    return data


def insert_alias(qq: int, alias: str):
    db.execute("INSERT INTO aliases (qq, alias) VALUES (?, ?)", (qq, alias))
    db.commit()


def select_alias(qq: int = 0, alias: str = ""):
    cursor = db.cursor()

    if qq != 0 and alias != "":
        cursor.execute("SELECT * FROM aliases WHERE qq = ? AND alias = ?", (qq, alias))
    elif qq != 0 and alias == "":
        cursor.execute("SELECT * FROM aliases WHERE qq = ?", (qq,))
    elif qq == 0 and alias != "":
        cursor.execute("SELECT * FROM aliases WHERE alias = ?", (alias,))
    else:
        cursor.execute("SELECT * FROM aliases")

    data = cursor.fetchall()
    cursor.close()
    return data


def parse_message(msg: Message) -> list[MessageSegment]:
    tokens = []

    for i in msg:
        if i.type == "at":
            tokens.append(i)
        elif i.type == "text":
            for j in i.data["text"].split():
                tokens.append(MessageSegment.text(j))

    return tokens


async def get_name(bot: Bot, group_id: int, user_id: int) -> str:
    try:
        info = await bot.get_group_member_info(group_id=group_id, user_id=user_id)
        return info["card"] if info["card"] != "" else info["nickname"]
    except:
        return str(user_id)


async def rule_group(event: GroupMessageEvent) -> bool:
    return event.group_id in config.groups


async def rule_admin(event: GroupMessageEvent) -> bool:
    return event.user_id in config.admins


cmd_add = on_command(
    "设精", is_type(GroupMessageEvent) & rule_group, force_whitespace=True
)


@cmd_add.handle()
async def fn_add(bot: Bot, event: GroupMessageEvent):
    if event.reply is None or event.reply.sender.user_id is None:
        return

    essence = ""

    for i in event.reply.message:
        if i.type in ["text", "face"]:
            essence += str(i)
        elif i.type == "at":
            essence += f"@{await get_name(bot,event.group_id,i.data['qq'])}"

    if essence == "":
        return

    data = select_essence(event.reply.sender.user_id, essence)

    if data != []:
        return

    insert_essence(event.reply.sender.user_id, essence)
    await cmd_add.send("设精成功！")


cmd_show = on_command(
    "爆典", is_type(GroupMessageEvent) & rule_group, force_whitespace=True
)


@cmd_show.handle()
async def fn_show(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    if len(args) == 0:
        data = select_essence()

        if data == []:
            return

        _, qq, essence = random.choice(data)
        data = select_alias(qq)

        if data != []:
            name = random.choice(data)[2]
        else:
            name = await get_name(bot, event.group_id, qq)

        await cmd_show.send(f"{name}：\n" + Message(essence))
        return

    for i in parse_message(args):
        if i.type == "at":
            qq = i.data["qq"]
        elif i.type == "text":
            data = select_alias(alias=i.data["text"])

            if data == []:
                continue

            qq = data[0][1]
        else:
            continue

        data = select_essence(qq)

        if data == []:
            continue

        _, qq, essence = random.choice(data)
        await cmd_show.send(Message(essence))


cmd_control = on_command(
    "设精管理", is_type(GroupMessageEvent) & rule_group, force_whitespace=True
)


@cmd_control.handle()
async def fn_control(args: Message = CommandArg()):
    tokens = parse_message(args)

    if len(tokens) == 0 or tokens[0].type != "text":
        return

    match tokens[0].data["text"]:
        case "alias":
            await sub_alias(tokens[1:])


async def sub_alias(tokens: list[MessageSegment]):
    if len(tokens) == 0 or tokens[0].type != "at":
        return

    qq = tokens[0].data["qq"]

    if len(tokens) == 1:
        data = select_alias(qq)

        if data == []:
            return

        await cmd_control.send("\n".join([i[2] for i in data]))
        return

    for i in tokens[1:]:
        if i.type != "text":
            continue

        alias = i.data["text"]
        data = select_alias(qq, alias)

        if data != []:
            continue

        insert_alias(qq, alias)
        await cmd_control.send(f"设置成功！")
