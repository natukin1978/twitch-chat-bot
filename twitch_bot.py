import asyncio
import datetime
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
        self.login_channel = g.config["twitch"]["loginChannel"]
        super().__init__(
            token=g.config["twitch"]["accessToken"],
            prefix="!",
            initial_channels=[self.login_channel],
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

    async def send_message(self, json_data: dict[str, any], answerLevel: int):
        if g.config["phantomJsCloud"]["apiKey"]:
            content = json_data["content"]
            url = TwitchBot.find_url(content)
            if url:
                # Webスクレイピングを表明する
                channel = self.get_channel(self.login_channel)
                await channel.send(g.WEB_SCRAPING_MESSAGE)

                if "www.twitch.tv" in url:
                    content = await TwitchBot.web_scraping(url, "html")
                    contents_list = TwitchBot.get_all_contents(
                        content, "[class*='channel-info-content']"
                    )
                    content = "\n".join(contents_list)
                else:
                    content = await TwitchBot.web_scraping(url, "plainText")

                json_data["content"] = g.WEB_SCRAPING_PROMPT + "\n" + content
                answer_length = g.config["fuyukaApi"]["answerLength"]["webScraping"]
                OneCommeUsers.update_additional_requests(json_data, answer_length)
                answerLevel = 100  # 常に回答してください

        needs_response = is_hit_by_message_json(answerLevel, json_data)
        await Fuyuka.send_message_by_json_with_buf(json_data, needs_response)

    async def do_time_signal(self, message: str):
        while True:
            now = datetime.datetime.now()
            next_hour = now.replace(
                minute=0, second=0, microsecond=0
            ) + datetime.timedelta(hours=1)
            wait_seconds = (next_hour - now).seconds
            await asyncio.sleep(wait_seconds)

            json_data = create_message_json()
            json_data["content"] = message
            answerLevel = 100
            await self.send_message(json_data, answerLevel)

    async def event_message(self, message: twitchio.Message):
        if message.echo:
            return

        id = message.author.name
        if id in g.set_exclude_id:
            # 無視するID
            return

        if message.content.startswith("!"):
            await self.handle_commands(message)
            return

        emotes = []
        add_emotes(emotes, message)
        text = remove_emote(message.content, emotes)
        if not text:
            return

        json_data = create_message_json(message)
        json_data["content"] = text
        answerLevel = g.config["fuyukaApi"]["answerLevel"]
        await self.send_message(json_data, answerLevel)

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
        answer_length = g.config["fuyukaApi"]["answerLength"]["aiCmd"]
        OneCommeUsers.update_additional_requests(json_data, answer_length)
        await Fuyuka.send_message_by_json_with_buf(json_data, True)
