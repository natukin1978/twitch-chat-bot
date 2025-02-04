import asyncio
import json
import logging

import twitchio

import global_value as g

g.app_name = "twitch_chat_bot"

from config_helper import readConfig
from fuyuka_helper import Fuyuka
from one_comme_users import OneCommeUsers
from random_helper import is_hit
from text_helper import readText
from twitch_bot import TwitchBot
from twitch_message_helper import create_message_json
from websocket_helper import websocket_listen_forever

g.WEB_SCRAPING_PROMPT = readText("prompts/web_scraping_prompt.txt")
g.ADDITIONAL_REQUESTS_PROMPT = readText("prompts/additional_requests_prompt.txt")
g.WEB_SCRAPING_MESSAGE = readText("messages/web_scraping_message.txt")

g.config = readConfig()

# ロガーの設定
logging.basicConfig(level=logging.INFO)

g.map_is_first_on_stream = {}
g.one_comme_users = OneCommeUsers.read_one_comme_users()
g.set_exclude_id = set(readText("exclude_id.txt").splitlines())
g.set_needs_response = set()
g.talker_name = ""
g.websocket_fuyuka_chat = None
g.websocket_fuyuka_flow_story = None


async def main():
    def get_fuyukaApi_baseUrl() -> str:
        conf_fa = g.config["fuyukaApi"]
        if not conf_fa:
            return ""
        return conf_fa["baseUrl"]

    def has_keywords_response(message: str) -> bool:
        conf_fa = g.config["fuyukaApi"]
        if not conf_fa:
            return False
        response_keywords = conf_fa["responseKeywords"]
        return next(filter(lambda v: v in message, response_keywords), None)

    def has_keywords_exclusion(message: str) -> bool:
        conf_fa = g.config["fuyukaApi"]
        if not conf_fa:
            return False
        exclusion_keywords = conf_fa["exclusionKeywords"]
        return next(filter(lambda v: v in message, exclusion_keywords), None)

    def get_neoInnerApi_baseUrl() -> str:
        conf_nia = g.config["neoInnerApi"]
        if not conf_nia:
            return ""
        return conf_nia["baseUrl"]

    # 注意. 判定フラグを削除するため、受信ハンドラでこの関数を複数回呼んではいけない
    def is_needs_response(json_data: dict[str, any]) -> bool:
        if "youtube_chat_bot" in json_data["id"]:
            return True

        request_dateTime = json_data["request"]["dateTime"]
        if request_dateTime not in g.set_needs_response:
            return False

        g.set_needs_response.discard(request_dateTime)
        return True

    def set_ws_fuyuka_chat(ws) -> None:
        g.websocket_fuyuka_chat = ws

    def set_ws_fuyuka_flow_story(ws) -> None:
        g.websocket_fuyuka_flow_story = ws

    async def recv_fuyuka_chat_response(message: str) -> None:
        try:
            json_data = json.loads(message)
            if not is_needs_response(json_data):
                return
            response_text = json_data["response"]
            if not response_text:
                return
            await client.get_channel(g.config["twitch"]["loginChannel"]).send(
                response_text
            )
        except json.JSONDecodeError:
            pass

    async def recv_message(message: str) -> None:
        try:
            data = json.loads(message)
            if type(data) is not dict:
                raise json.JSONDecodeError("result value was not dict", "", "")
            # JSONとして処理する
            g.talker_name = data["talkerName"]
        except json.JSONDecodeError:
            # プレーンテキストとして処理する
            message = message.strip()
            if len(message) <= 1 or has_keywords_exclusion(message):
                # 1文字や除外キーワードは取り込まない
                return

            is_response = has_keywords_response(message)
            answerLevel = 2
            json_data = create_message_json()
            json_data["id"] = g.config["twitch"]["loginChannel"]
            json_data["displayName"] = g.talker_name
            json_data["content"] = message.strip()
            OneCommeUsers.update_message_json(json_data)
            if is_response or is_hit(answerLevel):
                if is_response:
                    # レスポンス有効時は追加の要望を無効化
                    del json_data["additionalRequests"]
                await Fuyuka.send_message_by_json_with_buf(json_data, True)
            else:
                await Fuyuka.flow_story_by_json(json_data)

    print("前回の続きですか？(y/n) ", end="")
    is_continue = input() == "y"
    if is_continue:
        if OneCommeUsers.load_is_first_on_stream():
            print("挨拶キャッシュを復元しました。")
        # if await Fuyuka.restore():
        #     print("Fuyukaの会話履歴を復元しました。")

    client = twitchio.Client(
        token=g.config["twitch"]["accessToken"],
        initial_channels=[g.config["twitch"]["loginChannel"]],
    )
    await client.connect()

    bot = TwitchBot()
    await bot.connect()

    fuyukaApi_baseUrl = get_fuyukaApi_baseUrl()
    if fuyukaApi_baseUrl:
        asyncio.create_task(
            websocket_listen_forever(
                f"{fuyukaApi_baseUrl}/chat/{g.app_name}",
                recv_fuyuka_chat_response,
                set_ws_fuyuka_chat,
            )
        )

        asyncio.create_task(
            websocket_listen_forever(
                f"{fuyukaApi_baseUrl}/flow_story", None, set_ws_fuyuka_flow_story
            )
        )

    neoInnerApi_baseUrl = get_neoInnerApi_baseUrl()
    if neoInnerApi_baseUrl:
        asyncio.create_task(
            websocket_listen_forever(f"{neoInnerApi_baseUrl}/textonly", recv_message)
        )

    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        pass
    finally:
        pass


if __name__ == "__main__":
    asyncio.run(main())
