from lxml import html
from lxml.html import HtmlElement
from nonebot import get_driver, on_message
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.rule import is_type
from openai import OpenAI
from requests import get

config = get_driver().config
chat_client = OpenAI(
    api_key=config.api_key,
    base_url=config.base_url,
)


def parse_element(element: HtmlElement, unknown_tags: set) -> str:
    content = (element.text or "").strip()

    for i in element:
        content += f"{parse_element(i, unknown_tags)}{(i.tail or '').strip()}"

    match element.tag:
        case "a" | "div" | "h2" | "h3" | "h4" | "h5" | "h6" | "ol" | "pre" | "ul":
            return content
        case "img":
            return "[图片]"
        case "li":
            return f"• {content}\n"
        case "br" | "code" | "p":
            return f"{content}\n"
        case _:
            unknown_tags.add(element.tag)
            return ""


def parse_v2ex(url: str) -> tuple[str, str, set[str]]:
    response = get(url)
    tree = html.fromstring(response.text)
    title = tree.xpath("//h1/text()")[0]
    body = tree.xpath("//div[@class='topic_content']")[0]
    unknown_tags = set()
    content = parse_element(body, unknown_tags)
    return title, content, unknown_tags


def legal_check(content: str) -> bool:
    return (
        chat_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个负责检查文章标题和内容是否违法违规的程序，你会将用户消息当作程序的输入，在输出中用少量文字分析该文章是否违法违规，然后在输出的末尾另起一行，该行只有一个以'<'开头、'>'结尾的布尔值， <true> 表示该文章违法违规， <false> 表示该文章不违法违规\n违法违规指的是：该文章涉及中华人民共和国政治敏感内容，或者涉及色情、赌博、毒品、暴力、恐怖主义等违法违规内容",
                },
                {
                    "role": "user",
                    "content": content,
                },
            ],
            temperature=0,
        )
        .choices[0]
        .message.content
        == "<false>"
    )


cmd_msg = on_message(is_type(GroupMessageEvent))


@cmd_msg.handle()
async def fn_msg(event: GroupMessageEvent):
    message = event.get_plaintext()

    if not message.startswith("https://www.v2ex.com/t/"):
        return

    title, content, unknown_tags = parse_v2ex(message)

    if len(content) > 256:
        content = f"{content[:256]}\n\n..."

    message = f"标题：\n{title}\n\n内容：\n{content}"

    if not legal_check(message):
        await cmd_msg.send("该链接内容疑似违法违规，请勿点击！")
        return

    if unknown_tags:
        message += f"\n\n发现未知标签，请联系管理员：\n{unknown_tags}"

    await cmd_msg.send(message)
