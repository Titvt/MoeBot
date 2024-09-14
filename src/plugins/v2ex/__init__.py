from lxml import html
from lxml.html import HtmlElement
from nonebot import on_message
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.rule import is_type
from requests import get


def parse_element(element: HtmlElement) -> str:
    content = (element.text or "").strip()

    for i in element:
        content += f"{parse_element(i)}{(i.tail or '').strip()}"

    match element.tag:
        case "a" | "div" | "h2" | "h3" | "h4" | "h5" | "h6" | "ol" | "pre" | "ul":
            return content
        case "img":
            return "[图片]"
        case "li":
            return f"• {content}\n"
        case "code" | "p":
            return f"{content}\n"
        case _:
            return ""


def parse_v2ex(url: str) -> tuple[str, str]:
    response = get(url)
    tree = html.fromstring(response.text)
    title = tree.xpath("//h1/text()")[0]
    body = tree.xpath("//div[@class='markdown_body']")[0]
    content = parse_element(body)
    return title, content


cmd_msg = on_message(is_type(GroupMessageEvent))


@cmd_msg.handle()
async def fn_msg(event: GroupMessageEvent):
    message = event.get_plaintext()

    if not message.startswith("https://www.v2ex.com/t/"):
        return

    title, content = parse_v2ex(message)

    if len(content) > 1024:
        content = f"{content[:1024]}\n\n..."

    await cmd_msg.send(f"标题：\n{title}\n\n内容：\n{content}")
