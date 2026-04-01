import asyncio
import datetime
import json
import logging
import re
from typing import TYPE_CHECKING

import aiohttp
import asqlite
import twitchio
from bs4 import BeautifulSoup
from twitchio import eventsub
from twitchio.ext import commands

if TYPE_CHECKING:
    import sqlite3

import global_value as g
from emote_helper import add_emotes, remove_emote
from function_skipper import FunctionSkipper
from fuyuka_helper import Fuyuka
from keywords_helper import has_keywords_exclusion, has_keywords_response
from one_comme_users import OneCommeUsers
from random_helper import is_hit_by_message_json
from time_signal_helper import calculate_next_time
from twitch_message_helper import (
    create_message_json,
    create_message_json_from_twitchio_message,
)

logger = logging.getLogger(__name__)


class TwitchBot(commands.AutoBot):
    def __init__(
        self, *, token_database: asqlite.Pool, subs: list[eventsub.SubscriptionPayload]
    ) -> None:
        self.token_database = token_database

        ctw = g.config["twitch"]
        super().__init__(
            client_id=ctw["clientId"],
            client_secret=ctw["clientSecret"],
            bot_id=ctw["botId"],
            owner_id=ctw["ownerId"],
            prefix="!",
            subscriptions=subs,
            force_subscribe=True,
        )

    async def setup_hook(self) -> None:
        # Add our component which contains our commands...
        await self.add_component(MyComponent(self))

    async def event_oauth_authorized(
        self, payload: twitchio.authentication.UserTokenPayload
    ) -> None:
        await self.add_token(payload.access_token, payload.refresh_token)

        if not payload.user_id:
            return

        if payload.user_id == self.bot_id:
            # We usually don't want subscribe to events on the bots channel...
            return

        # A list of subscriptions we would like to make to the newly authorized channel...
        subs: list[eventsub.SubscriptionPayload] = [
            eventsub.ChatMessageSubscription(
                broadcaster_user_id=payload.user_id, user_id=self.bot_id
            ),
        ]

        resp: twitchio.MultiSubscribePayload = await self.multi_subscribe(subs)
        if resp.errors:
            logger.warning(
                "Failed to subscribe to: %r, for user: %s", resp.errors, payload.user_id
            )

    async def add_token(
        self, token: str, refresh: str
    ) -> twitchio.authentication.ValidateTokenPayload:
        # Make sure to call super() as it will add the tokens interally and return us some data...
        resp: twitchio.authentication.ValidateTokenPayload = await super().add_token(
            token, refresh
        )

        # Store our tokens in a simple SQLite Database when they are authorized...
        query = """
        INSERT INTO tokens (user_id, token, refresh)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET
            token = excluded.token,
            refresh = excluded.refresh;
        """

        async with self.token_database.acquire() as connection:
            await connection.execute(query, (resp.user_id, token, refresh))

        logger.info("Added token to the database for user: %s", resp.user_id)
        return resp

    async def event_ready(self) -> None:
        logger.info("Successfully logged in as: %s", self.bot_id)

    async def send_message(self, message: str) -> None:
        ctw = g.config["twitch"]
        user = self.create_partialuser(user_id=ctw["ownerId"])
        await user.send_message(sender=ctw["botId"], message=message)

    def get_mycomponent(self) -> any:
        return self.get_component("MyComponent")


class MyComponent(commands.Component):
    # An example of a Component with some simple commands and listeners
    # You can use Components within modules for a more organized codebase and hot-reloading.

    def __init__(self, bot: TwitchBot) -> None:
        # Passing args is not required...
        # We pass bot here as an example...
        self.bot = bot

    @staticmethod
    def find_url(text: str) -> str:
        # 正規表現パターン
        # このパターンは、httpやhttpsプロトコルを含むURLを検索します。
        # 特に、ドメイン名やサブドメイン、ポート番号などを考慮しています。
        RE_URL = r"https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
        urls = re.findall(RE_URL, text)
        if urls:
            return urls[0]  # 最初のURLを返す
        return ""

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

    async def send_message(self, json_data: dict[str, any], answer_level: int):
        answer_length = g.config["fuyukaApi"]["answerLength"]["default"]

        if g.config["phantomJsCloud"]["apiKey"]:
            content = json_data["content"]
            url = self.find_url(content)
            if url:
                logger.info("web_scraping: " + url)
                if "www.twitch.tv" in url:
                    content = await self.web_scraping(url, "html")
                    contents_list = self.get_all_contents(
                        content, "[class*='channel-info-content']"
                    )
                    content = "\n".join(contents_list)
                else:
                    content = await TwitchBot.web_scraping(url, "plainText")

                json_data["content"] = g.WEB_SCRAPING_PROMPT + "\n" + content
                answer_length = g.config["fuyukaApi"]["answerLength"]["webScraping"]
                answer_level = 100  # 常に回答してください

        needs_response = is_hit_by_message_json(answer_level, json_data)
        if not needs_response:
            answer_length = 0
        OneCommeUsers.update_additional_requests(json_data, answer_length)
        await Fuyuka.send_message_by_json_with_buf(json_data, needs_response)

    # An example of listening to an event
    # We use a listener in our Component to display the messages received.
    @commands.Component.listener()
    async def event_message(self, payload: twitchio.ChatMessage) -> None:
        if payload.chatter.id == self.bot.bot_id:
            return

        id = payload.chatter.name
        if id in g.set_exclude_id:
            # 無視するID
            return

        if payload.text.startswith("!"):
            # await self.handle_commands(payload)
            return

        # fragmentsを使ってテキスト部分だけを繋ぎ合わせる
        # fragment.type が "text" のものだけを取り出す
        text = "".join(
            fragment.text for fragment in payload.fragments if fragment.type == "text"
        )

        # 前後の余計な空白を整える
        text = text.strip()
        if not text:
            return

        if has_keywords_exclusion(text):
            # 除外キーワードは取り込まない
            return

        json_data = create_message_json_from_twitchio_message(payload, text)
        answer_level = 0
        if has_keywords_response(text):
            answer_level = 100  # 常に回答してください
        else:
            answer_level = g.config["fuyukaApi"]["answerLevel"]
        await self.send_message(json_data, answer_level)

    @commands.command()
    async def ai(self, ctx: commands.Context, *, message: str) -> None:
        """Command which repeats what the invoker sends.

        !ai <message>
        """
        json_data = create_message_json_from_twitchio_message(ctx.message, message)
        answer_length = g.config["fuyukaApi"]["answerLength"]["aiCmd"]
        needs_response = True
        OneCommeUsers.update_additional_requests(json_data, answer_length)
        await Fuyuka.send_message_by_json_with_buf(json_data, needs_response)


async def setup_database(
    db: asqlite.Pool,
) -> tuple[list[tuple[str, str]], list[eventsub.SubscriptionPayload]]:
    # Create our token table, if it doesn't exist..
    # You should add the created files to .gitignore or potentially store them somewhere safer
    # This is just for example purposes...

    query = """CREATE TABLE IF NOT EXISTS tokens(user_id TEXT PRIMARY KEY, token TEXT NOT NULL, refresh TEXT NOT NULL)"""
    async with db.acquire() as connection:
        await connection.execute(query)

        # Fetch any existing tokens...
        rows: list[sqlite3.Row] = await connection.fetchall("""SELECT * from tokens""")

        tokens: list[tuple[str, str]] = []
        subs: list[eventsub.SubscriptionPayload] = []

        ctw = g.config["twitch"]
        bot_id = ctw["botId"]

        for row in rows:
            tokens.append((row["token"], row["refresh"]))

            if row["user_id"] == bot_id:
                continue

            subs.extend(
                [
                    eventsub.ChatMessageSubscription(
                        broadcaster_user_id=row["user_id"], user_id=bot_id
                    )
                ]
            )

    return tokens, subs
