import json
import logging
import re

import aiohttp
import twitchio
from bs4 import BeautifulSoup
from twitchio.ext import commands

import global_value as g
from emote_helper import add_emotes, remove_emote
from fuyuka_helper import Fuyuka
from one_comme_users import OneCommeUsers
from random_helper import is_hit_by_message_json
from twitch_message_helper import create_message_json

logger = logging.getLogger(__name__)


class TwitchBot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=g.config["twitch"]["accessToken"],
            prefix="!",
            initial_channels=[g.config["twitch"]["loginChannel"]],
        )

    @staticmethod
    def find_url(text: str) -> str:
        # 正規表現パターン
        # このパターンは、httpやhttpsプロトコルを含むURLを検索します。
        # 特に、ドメイン名やサブドメイン、ポート番号などを考慮しています。
        RE_URL = r'\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`()\[\]{};:\'".,<>?«»“”‘’]))'

        urls = re.findall(RE_URL, text)
        if not urls:
            return ""

        # 最初の要素だけを返す
        return urls[0][0]

    @staticmethod
    async def web_scraping(url: str, renderType: str) -> str:
        param = {
            "url": url,
            "renderType": renderType,
        }
        API_URL = (
            "http://PhantomJScloud.com/api/browser/v2/"
            + g.config["phantomJsCloud"]["apiKey"]
            + "/"
        )
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, data=json.dumps(param)) as response:
                return await response.text()

    @staticmethod
    def get_all_contents(html_content: str, target_selector: str) -> list:
        soup = BeautifulSoup(html_content, "html.parser")
        elem = soup.select_one(target_selector)
        elem_strings = elem.stripped_strings
        return [elem_string for elem_string in elem_strings]

    async def event_message(self, msg: twitchio.Message):
        if msg.echo:
            return

        id = msg.author.name
        if id in g.set_exclude_id:
            # 無視するID
            return

        if msg.content.startswith("!"):
            await self.handle_commands(msg)
            return

        emotes = []
        add_emotes(emotes, msg)
        text = remove_emote(msg.content, emotes)
        if not text:
            return

        json_data = create_message_json(msg)
        json_data["content"] = text
        answerLevel = g.config["fuyukaApi"]["answerLevel"]

        if g.config["phantomJsCloud"]["apiKey"]:
            url = TwitchBot.find_url(text)
            if url:
                # Webスクレイピングを表明する
                await msg.channel.send(g.WEB_SCRAPING_MESSAGE)

                content = None
                if "www.twitch.tv" in url:
                    content = await TwitchBot.web_scraping(url, "html")
                    contents_list = TwitchBot.get_all_contents(
                        content, "[class*='channel-info-content']"
                    )
                    content = "\n".join(contents_list)
                else:
                    content = await TwitchBot.web_scraping(url, "plainText")

                json_data["content"] = g.WEB_SCRAPING_PROMPT + "\n" + content
                # Webの内容なのでちょっと大目に見る
                OneCommeUsers.update_additional_requests(json_data, 120)
                answerLevel = 100  # 常に回答してください

        needs_response = is_hit_by_message_json(answerLevel, json_data)
        await Fuyuka.send_message_by_json_with_buf(json_data, needs_response)

    @staticmethod
    def get_cmd_value(content: str) -> str:
        pattern = r"^![^ ]+ (.*?)$"
        match = re.search(pattern, content)
        if not match:
            logger.debug("Not match: " + content)
            return ""

        return match.group(1)

    @commands.command(name="ai")
    async def cmd_ai(self, ctx: commands.Context):
        text = TwitchBot.get_cmd_value(ctx.message.content)

        json_data = create_message_json(ctx.message)
        json_data["content"] = text
        OneCommeUsers.update_additional_requests(json_data, 70)
        await Fuyuka.send_message_by_json_with_buf(json_data, True)
