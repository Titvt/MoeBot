import math
from sqlite3 import connect
from time import time

import matplotlib.pyplot as plt
import pandas as pd
from jieba.analyse import extract_tags
from matplotlib.dates import SU, DateFormatter, WeekdayLocator
from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.rule import is_type
from seaborn import lineplot
from wordcloud import WordCloud

from src.bus import send

AVAIL_CLOUD: float = 0
AVAIL_STATISTICS: float = 0

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
    global AVAIL_CLOUD
    now = time()

    if now < AVAIL_CLOUD:
        await send(event, "别急！")
        return

    AVAIL_CLOUD = now + 10

    if len(args) == 0:
        messages = select_messages(event.group_id, event.user_id)
    elif args[0].type == "at":
        messages = select_messages(event.group_id, args[0].data["qq"])
    elif args[0].type == "text" and args[0].data["text"].strip().lower() == "all":
        messages = select_messages(event.group_id)
    else:
        await send(event, "不对！")
        return

    if len(messages) < 40:
        await send(event, "太少！")
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
        frequencies[i] = math.log(frequencies[i] + math.e - 1)

    cloud = WordCloud(
        "SmileySans-Oblique.ttf",
        1280,
        720,
        prefer_horizontal=1,
        max_words=400,
        background_color="white",
        max_font_size=180,
    )
    cloud.generate_from_frequencies(frequencies)
    cloud.to_file("word_cloud.png")

    with open("word_cloud.png", "rb") as f:
        await send(event, MessageSegment.image(f.read()))


cmd_statistics = on_command(
    "发言统计", is_type(GroupMessageEvent), force_whitespace=True
)


@cmd_statistics.handle()
async def fn_statistics(event: GroupMessageEvent, args: Message = CommandArg()):
    global AVAIL_STATISTICS
    now = time()

    if now < AVAIL_STATISTICS:
        await send(event, "别急！")
        return

    AVAIL_STATISTICS = now + 10

    if len(args) == 0:
        user_id = event.user_id
    elif args[0].type == "at":
        user_id = args[0].data["qq"]
    elif args[0].type == "text" and args[0].data["text"].strip().lower() == "all":
        user_id = 0
    else:
        await send(event, "不对！")
        return

    if user_id == 0:
        data = pd.read_sql_query(
            "SELECT time FROM messages WHERE group_id = ?", db, params=(event.group_id,)
        )
    else:
        data = pd.read_sql_query(
            "SELECT time FROM messages WHERE group_id = ? AND user_id = ?",
            db,
            params=(event.group_id, user_id),
        )

    data["time"] = pd.to_datetime(data["time"], unit="s")
    data = data.groupby(data["time"].dt.date).size()
    plt.figure(figsize=(16, 9), dpi=80)
    lineplot(data, marker="o")
    axis = plt.gca()
    axis.xaxis.set_major_formatter(DateFormatter("%m.%d"))
    axis.xaxis.set_major_locator(WeekdayLocator(SU, 1))
    plt.xlabel("")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("statistics.png", dpi=80)
    plt.close()

    with open("statistics.png", "rb") as f:
        await send(event, MessageSegment.image(f.read()))
