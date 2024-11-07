from sqlite3 import connect

from nonebot import get_driver, on_command, on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.params import CommandArg
from nonebot.rule import is_type

ban_cache = {}
config = get_driver().config
db = connect("files/ban.db")
db.execute(
    "CREATE TABLE IF NOT EXISTS bans (id INTEGER PRIMARY KEY AUTOINCREMENT, group_id INTEGER, ban TEXT)"
)


def insert_ban(group_id: int, ban: str):
    db.execute(
        "INSERT INTO bans (group_id, ban) VALUES (?, ?)",
        (group_id, ban),
    )
    db.commit()


def delete_ban(group_id: int, ban: str):
    db.execute(
        "DELETE FROM bans WHERE group_id = ? AND ban = ?",
        (group_id, ban),
    )
    db.commit()


def select_bans(group_id: int) -> list[str]:
    cursor = db.cursor()
    cursor.execute("SELECT ban FROM bans WHERE group_id = ?", (group_id,))
    data = cursor.fetchall()
    cursor.close()
    return [row[0] for row in data]


cmd_msg = on_message(is_type(GroupMessageEvent))


@cmd_msg.handle()
async def fn_msg(bot: Bot, event: GroupMessageEvent):
    if event.user_id in config.ban_admin:
        return

    if event.group_id not in ban_cache:
        ban_cache[event.group_id] = select_bans(event.group_id)

    bans = ban_cache[event.group_id]

    if not bans:
        return

    message = event.get_plaintext()

    for ban in bans:
        if ban in message:
            await bot.delete_msg(message_id=event.message_id)
            await bot.set_group_ban(
                group_id=event.group_id, user_id=event.user_id, duration=300
            )
            await cmd_msg.send("你发送了违禁词，禁言！")
            return


cmd_add = on_command("添加违禁词", is_type(GroupMessageEvent), force_whitespace=True)


@cmd_add.handle()
async def fn_add(event: GroupMessageEvent, args: Message = CommandArg()):
    if event.user_id not in config.ban_admin:
        await cmd_add.send("无权限！")
        return

    if len(args) != 1 or args[0].type != "text":
        await cmd_add.send("错误！")
        return

    ban = args[0].data["text"].strip()

    if ban == "":
        await cmd_add.send("错误！")
        return

    if event.group_id not in ban_cache:
        ban_cache[event.group_id] = select_bans(event.group_id)

    bans = ban_cache[event.group_id]

    if ban in bans:
        await cmd_add.send("已存在！")
        return

    insert_ban(event.group_id, ban)
    ban_cache[event.group_id] = select_bans(event.group_id)
    await cmd_add.send("添加成功！")


cmd_delete = on_command("删除违禁词", is_type(GroupMessageEvent), force_whitespace=True)


@cmd_delete.handle()
async def fn_delete(event: GroupMessageEvent, args: Message = CommandArg()):
    if event.user_id not in config.ban_admin:
        await cmd_add.send("无权限！")
        return

    if len(args) != 1 or args[0].type != "text":
        await cmd_add.send("错误！")
        return

    ban = args[0].data["text"].strip()

    if ban == "":
        await cmd_add.send("错误！")
        return

    if event.group_id not in ban_cache:
        ban_cache[event.group_id] = select_bans(event.group_id)

    bans = ban_cache[event.group_id]

    if ban not in bans:
        await cmd_add.send("不存在！")
        return

    delete_ban(event.group_id, ban)
    ban_cache[event.group_id] = select_bans(event.group_id)
    await cmd_add.send("删除成功！")


cmd_list = on_command("违禁词列表", is_type(GroupMessageEvent))


@cmd_list.handle()
async def fn_list(event: GroupMessageEvent):
    if event.group_id not in ban_cache:
        ban_cache[event.group_id] = select_bans(event.group_id)

    bans = ban_cache[event.group_id]

    if not bans:
        await cmd_list.send("无违禁词！")
        return

    await cmd_list.send("\n".join(bans))
