import asyncio
import json
import socket
import sys

import twitchio
import websockets

import global_value as g
from config_helper import readConfig
from fuyuka_helper import Fuyuka
from one_comme_users import OneCommeUsers
from random_helper import is_hit
from text_helper import readText
from twitch_bot import TwitchBot
from twitch_message_helper import create_message_json

g.WEB_SCRAPING_PROMPT = readText("prompts/web_scraping_prompt.txt")
g.ADDITIONAL_REQUESTS_PROMPT = readText("prompts/additional_requests_prompt.txt")
g.WEB_SCRAPING_MESSAGE = readText("messages/web_scraping_message.txt")

g.config = readConfig()

g.map_is_first_on_stream = {}
g.one_comme_users = OneCommeUsers.read_one_comme_users()
g.set_exclude_id = set(readText("exclude_id.txt").splitlines())
g.talker_name = ""
g.talk_buffers = ""
g.websocket_fuyuka = None


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

    def set_ws_fuyuka(ws) -> None:
        g.websocket_fuyuka = ws

    async def recv_fuyuka_response(message: str) -> None:
        try:
            json_data = json.loads(message)
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
            talk_buffers_len = len(g.talk_buffers)
            answerLevel = 2
            if is_response or talk_buffers_len > 1000 or is_hit(answerLevel):
                json_data = create_message_json()
                json_data["id"] = g.config["twitch"]["loginChannel"]
                json_data["displayName"] = g.talker_name
                json_data["content"] = message.strip()
                OneCommeUsers.update_message_json(json_data)
                if is_response:
                    # レスポンス有効時は追加の要望を無効化
                    del json_data["additionalRequests"]
                await Fuyuka.send_message_by_json_with_buf(json_data)
            else:
                if talk_buffers_len > 0:
                    g.talk_buffers += " "
                g.talk_buffers += message

    async def websocket_listen_forever(
        websocket_uri: str, handle_message, handle_set_ws=None
    ) -> None:
        reply_timeout = 60
        ping_timeout = 15
        sleep_time = 5
        while True:
            # outer loop restarted every time the connection fails
            try:
                async with websockets.connect(websocket_uri) as ws:
                    if handle_set_ws:
                        handle_set_ws(ws)
                    while True:
                        # listener loop
                        try:
                            message = await asyncio.wait_for(
                                ws.recv(), timeout=reply_timeout
                            )
                            await handle_message(message)
                        except (
                            asyncio.TimeoutError,
                            websockets.exceptions.ConnectionClosed,
                        ):
                            try:
                                pong = await ws.ping()
                                await asyncio.wait_for(pong, timeout=ping_timeout)
                                continue
                            except:
                                await asyncio.sleep(sleep_time)
                                break
            except Exception as e:
                print(e, file=sys.stderr)
                await asyncio.sleep(sleep_time)
                continue
            finally:
                if handle_set_ws:
                    handle_set_ws(None)

    print("前回の続きですか？(y/n)")
    is_continue = input() == "y"
    if is_continue and OneCommeUsers.load_is_first_on_stream():
        print("挨拶キャッシュを復元しました。")

    client = twitchio.Client(
        token=g.config["twitch"]["accessToken"],
        initial_channels=[g.config["twitch"]["loginChannel"]],
    )
    await client.connect()

    bot = TwitchBot()
    await bot.connect()

    fuyukaApi_baseUrl = get_fuyukaApi_baseUrl()
    if fuyukaApi_baseUrl:
        websocket_uri = f"{fuyukaApi_baseUrl}/chat/twitch_chat_bot"
        asyncio.create_task(
            websocket_listen_forever(websocket_uri, recv_fuyuka_response, set_ws_fuyuka)
        )

    neoInnerApi_baseUrl = get_neoInnerApi_baseUrl()
    if neoInnerApi_baseUrl:
        websocket_uri = f"{neoInnerApi_baseUrl}/textonly"
        asyncio.create_task(websocket_listen_forever(websocket_uri, recv_message))

    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        pass
    finally:
        pass


if __name__ == "__main__":
    asyncio.run(main())
