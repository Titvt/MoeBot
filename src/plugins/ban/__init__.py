from nonebot import get_driver, on_command, on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.params import CommandArg
from nonebot.rule import is_type

ban_map = {}
config = get_driver().config
cmd_msg = on_message(is_type(GroupMessageEvent))


@cmd_msg.handle()
async def fn_msg(bot: Bot, event: GroupMessageEvent):
    if event.group_id not in ban_map or len(ban_map[event.group_id]) == 0:
        return

    message = event.get_plaintext()

    for ban in ban_map[event.group_id]:
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
    global ban_map

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

    if event.group_id not in ban_map:
        ban_map[event.group_id] = set()

    ban_map[event.group_id].add(ban)
    await cmd_add.send("添加成功！")


cmd_delete = on_command("删除违禁词", is_type(GroupMessageEvent), force_whitespace=True)


@cmd_delete.handle()
async def fn_delete(event: GroupMessageEvent, args: Message = CommandArg()):
    global ban_map

    if event.user_id not in config.ban_admin:
        await cmd_add.send("无权限！")
        return

    if len(args) != 1 or args[0].type != "text":
        await cmd_add.send("错误！")
        return

    ban = args[0].data["text"].strip()

    if ban == "" or event.group_id not in ban_map or ban not in ban_map[event.group_id]:
        await cmd_add.send("错误！")
        return

    ban_map[event.group_id].remove(ban)
    await cmd_add.send("删除成功！")


cmd_list = on_command("违禁词列表", is_type(GroupMessageEvent))


@cmd_list.handle()
async def fn_list(event: GroupMessageEvent):
    global ban_map

    if event.group_id not in ban_map or len(ban_map[event.group_id]) == 0:
        await cmd_list.send("无违禁词！")
        return

    await cmd_list.send("\n".join(ban_map[event.group_id]))
