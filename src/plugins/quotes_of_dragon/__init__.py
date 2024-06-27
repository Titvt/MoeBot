from random import choice
from sqlite3 import connect

from jieba import cut
from nonebot import get_driver, on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message
from nonebot.params import CommandArg
from nonebot.rule import is_type
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

config = get_driver().config
db = connect("quotes_of_dragon.db")
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

    v = TfidfVectorizer().fit_transform([" ".join(cut(i)) for i in [text] + quotes])
    s = cosine_similarity(v[0], v[1:])[0]
    return choice(quotes) if max(s) < 0.01 else quotes[s.tolist().index(max(s))]


async def rule_group(event: GroupMessageEvent) -> bool:
    return event.group_id in config.groups


async def rule_admin(event: GroupMessageEvent) -> bool:
    return event.user_id in config.admins


cmd_quote = on_command(
    "龙语", is_type(GroupMessageEvent) & rule_group, force_whitespace=True
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
