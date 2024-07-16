from os import getcwd, remove
from os.path import join
from sqlite3 import connect
from time import time

from jieba.analyse import extract_tags
from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.rule import is_type
from wordcloud import WordCloud

avail_cloud = 0
db = connect("word_cloud.db")
db.execute(
    "CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, qq INTEGER, group_id INTEGER, message TEXT)"
)


def insert_message(qq: int, group_id: int, message: str):
    db.execute(
        "INSERT INTO messages (qq, group_id, message) VALUES (?, ?, ?)",
        (qq, group_id, message),
    )
    db.commit()


def select_messages(qq: int, group_id: int) -> list[tuple[int, int, int, str]]:
    cursor = db.cursor()

    if qq == 0:
        cursor.execute("SELECT * FROM messages WHERE group_id = ?", (group_id,))
    else:
        cursor.execute(
            "SELECT * FROM messages WHERE qq = ? AND group_id = ?", (qq, group_id)
        )

    data = cursor.fetchall()
    cursor.close()
    return data


cmd_msg = on_message(is_type(GroupMessageEvent))


@cmd_msg.handle()
async def fn_msg(event: GroupMessageEvent):
    message = event.get_plaintext()

    if message == "":
        return

    insert_message(event.user_id, event.group_id, message)


cmd_cloud = on_command("词云", is_type(GroupMessageEvent))


@cmd_cloud.handle()
async def fn_cloud(event: GroupMessageEvent, args: Message = CommandArg()):
    global avail_cloud
    now = time()

    if now < avail_cloud:
        await cmd_cloud.send("别急！")
        return

    avail_cloud = now + 10

    if len(args) == 0:
        messages = select_messages(0, event.group_id)
    elif args[0].type == "at":
        messages = select_messages(args[0].data["qq"], event.group_id)
    elif args[0].type == "text" and args[0].data["text"].strip().isnumeric():
        messages = select_messages(int(args[0].data["text"].strip()), event.group_id)
    else:
        await cmd_cloud.send("不对！")
        return

    if len(messages) < 20:
        await cmd_cloud.send("太少！")
        return

    frequencies = {}

    for i in messages:
        for j in extract_tags(i[3], None):
            if j in frequencies:
                frequencies[j] += 1
            else:
                frequencies[j] = 1

    cloud = WordCloud(
        "SmileySans-Oblique.ttf",
        1280,
        720,
        prefer_horizontal=1,
        background_color="white",
    )
    cloud.generate_from_frequencies(frequencies)
    cloud.to_file("word_cloud.png")
    await cmd_cloud.send(MessageSegment.image("file:///root/word_cloud.png"))
    remove("word_cloud.png")
