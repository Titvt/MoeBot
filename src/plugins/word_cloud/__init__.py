import math
from sqlite3 import connect
from time import time

from jieba.analyse import extract_tags
from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.rule import is_type
from wordcloud import WordCloud

avail_cloud = 0
db = connect("files/word_cloud.db")
db.execute(
    "CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, time TIMESTAMP, group_id INTEGER, user_id INTEGER, message TEXT)"
)


def insert_message(group_id: int, user_id: int, message: str):
    db.execute(
        "INSERT INTO messages (time, group_id, user_id, message) VALUES (?, ?, ?, ?)",
        (time(), group_id, user_id, message),
    )
    db.commit()


def select_messages(
    group_id: int, user_id: int = 0
) -> list[tuple[int, float, int, int, str]]:
    cursor = db.cursor()

    if user_id == 0:
        cursor.execute("SELECT * FROM messages WHERE group_id = ?", (group_id,))
    else:
        cursor.execute(
            "SELECT * FROM messages WHERE group_id = ? AND user_id = ?",
            (group_id, user_id),
        )

    data = cursor.fetchall()
    cursor.close()
    return data


cmd_msg = on_message(is_type(GroupMessageEvent))


@cmd_msg.handle()
async def fn_msg(event: GroupMessageEvent):
    message = event.get_plaintext().strip()

    if len(message) < 4:
        return

    insert_message(event.group_id, event.user_id, message)


cmd_cloud = on_command("词云", is_type(GroupMessageEvent), force_whitespace=True)


@cmd_cloud.handle()
async def fn_cloud(event: GroupMessageEvent, args: Message = CommandArg()):
    global avail_cloud
    now = time()

    if now < avail_cloud:
        await cmd_cloud.send("别急！")
        return

    avail_cloud = now + 10

    if len(args) == 0:
        messages = select_messages(event.group_id, event.user_id)
    elif args[0].type == "at":
        messages = select_messages(event.group_id, args[0].data["qq"])
    elif args[0].type == "text" and args[0].data["text"].strip().lower() == "all":
        messages = select_messages(event.group_id)
    else:
        await cmd_cloud.send("不对！")
        return

    if len(messages) < 40:
        await cmd_cloud.send("太少！")
        return

    frequencies = {}

    for i in messages:
        for j in extract_tags(
            i[4],
            400,
            allowPOS=(
                "a",
                "ad",
                "an",
                "b",
                "e",
                "eng",
                "i",
                "j",
                "l",
                "n",
                "nr",
                "nrfg",
                "nrt",
                "ns",
                "nt",
                "nz",
                "o",
                "q",
                "v",
                "vn",
                "y",
                "z",
            ),
        ):
            if j in frequencies:
                frequencies[j] += 1
            else:
                frequencies[j] = 1

    for i in frequencies:
        frequencies[i] = math.tanh(frequencies[i] / 40)

    cloud = WordCloud(
        "SmileySans-Oblique.ttf",
        1280,
        720,
        prefer_horizontal=1,
        max_words=400,
        background_color="white",
    )
    cloud.generate_from_frequencies(frequencies)
    cloud.to_file("word_cloud.png")

    with open("word_cloud.png", "rb") as f:
        await cmd_cloud.send(MessageSegment.image(f.read()))
