from random import choice
from sqlite3 import connect

import numpy as np
from jieba.analyse import extract_tags
from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message
from nonebot.params import CommandArg
from nonebot.rule import is_type
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

db = connect("files/quotes_of_dragon.db")
db.execute(
    "CREATE TABLE IF NOT EXISTS quotes (id INTEGER PRIMARY KEY AUTOINCREMENT, quote TEXT)"
)
cursor = db.cursor()
cursor.execute("SELECT * FROM quotes")
data = cursor.fetchall()
quotes = [i[1] for i in data]


def get_quote(text: str) -> str:
    if len(quotes) == 0:
        return ""

    if text == "":
        return choice(quotes)

    v = TfidfVectorizer().fit_transform(
        [" ".join(extract_tags(i, None)) for i in [text] + quotes]
    )
    s = cosine_similarity(v[0], v[1:])[0].flatten()

    if max(s) < 0.01:
        return choice(quotes)

    i = np.where(s >= 0.01)[0]
    j = s[i]
    return quotes[np.random.choice(i, p=j / np.sum(j))]


cmd_quote = on_command(
    "龙语（已禁用）", is_type(GroupMessageEvent), force_whitespace=True
)


@cmd_quote.handle()
async def fn_quote(event: GroupMessageEvent, args: Message = CommandArg()):
    if event.reply is None:
        quote = get_quote(args.extract_plain_text())
    else:
        quote = get_quote(event.reply.message.extract_plain_text())

    if quote == "":
        return

    await cmd_quote.send(quote)
