import asyncio
import json
import logging
import os
import sys

import twitchio

import global_value as g

g.app_name = "twitch_chat_bot"
g.base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

from config_helper import read_config
from extract_commands import extract_commands
from function_skipper import FunctionSkipper
from fuyuka_helper import Fuyuka
from one_comme_users import OneCommeUsers
from random_helper import is_hit
from text_helper import read_text, read_text_set
from twitch_bot import TwitchBot
from twitch_message_helper import create_message_json
from websocket_helper import websocket_listen_forever

g.WEB_SCRAPING_PROMPT = read_text("prompts/web_scraping_prompt.txt")
g.ADDITIONAL_REQUESTS_PROMPT = read_text("prompts/additional_requests_prompt.txt")
g.WEB_SCRAPING_MESSAGE = read_text("messages/web_scraping_message.txt")

g.config = read_config()

# ロガーの設定
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

g.map_is_first_on_stream = {}
g.one_comme_users = OneCommeUsers.read_one_comme_users()
g.set_exclude_id = read_text_set("exclude_id.txt")
g.set_needs_response = set()
g.talker_name = ""
g.websocket_fuyuka = None


async def main():
    def get_fuyukaApi_baseUrl() -> str:
        conf_fa = g.config["fuyukaApi"]
        if not conf_fa:
            return ""
        return conf_fa["baseUrl"]

    def has_keywords_response(message: str) -> bool:
        conf_nia = g.config["neoInnerApi"]
        if not conf_nia:
            return False
        response_keywords = conf_nia["responseKeywords"]
        return next(filter(lambda v: v in message, response_keywords), None)

    def has_keywords_exclusion(message: str) -> bool:
        conf_nia = g.config["neoInnerApi"]
        if not conf_nia:
            return False
        exclusion_keywords = conf_nia["exclusionKeywords"]
        return next(filter(lambda v: v in message, exclusion_keywords), None)

    def get_neoInnerApi_baseUrl() -> str:
        conf_nia = g.config["neoInnerApi"]
        if not conf_nia:
            return ""
        return conf_nia["baseUrl"]

    # 注意. 判定フラグを削除するため、受信ハンドラでこの関数を複数回呼んではいけない
    def is_needs_response(json_data: dict[str, any]) -> bool:
        request_id = json_data["request"]["id"]
        if fs_response.should_skip(request_id):
            # 同じIDで頻繁にレス返すのを抑止
            logger.info(f"間隔が空いてないのでスキップします。id = {request_id}")
            return False

        enable_chat_bots = {"youtube_chat_bot", "showroom_chat_bot", "openrec_chat_bot"}
        if json_data["id"] in enable_chat_bots:
            return True

        request_dateTime = json_data["request"]["dateTime"]
        if request_dateTime not in g.set_needs_response:
            return False

        g.set_needs_response.discard(request_dateTime)
        return True

    def set_ws_fuyuka(ws) -> None:
        g.websocket_fuyuka = ws

    async def recv_fuyuka_response(message: str) -> None:
        try:
            json_data = json.loads(message)
            response_text = json_data["response"]
            if not response_text:
                return

            commands = extract_commands(response_text)
            len_cmd = len(commands)
            if len_cmd > 1:
                # モデレーターコマンド
                cmd = commands[0]
                target_name = commands[1]

                mode_user_name = "fuyuka_ai"
                mode_user, ban_user = await client.fetch_users(
                    [mode_user_name, target_name]
                )
                p_user = client.create_user(mode_user.id, mode_user_name)

                cmd_result = None
                if cmd == "ban":
                    cmd_result = await mode_user.ban_user(
                        g.config["twitch"]["accessToken"],
                        mode_user.id,
                        ban_user.id,
                        "disrupted the broadcast.",
                    )
                elif cmd == "timeout":
                    if len_cmd < 3:
                        duration = 600
                    else:
                        duration = int(commands[2])
                    cmd_result = await mode_user.timeout_user(
                        g.config["twitch"]["accessToken"],
                        mode_user.id,
                        ban_user.id,
                        duration,
                        "disrupted the broadcast.",
                    )
                if cmd_result:
                    logger.info(cmd_result)

            if not is_needs_response(json_data):
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
            answerLevel = g.config["neoInnerApi"]["answerLevel"]
            json_data = create_message_json()
            json_data["id"] = g.config["twitch"]["loginChannel"]
            json_data["displayName"] = g.talker_name
            json_data["content"] = message.strip()
            OneCommeUsers.update_message_json(json_data)
            noisy = True
            if is_response or is_hit(answerLevel):
                if is_response:
                    # レスポンス有効時は追加の要望を無効化
                    del json_data["additionalRequests"]
                noisy = False

            json_data["noisy"] = noisy
            await Fuyuka.send_message_by_json_with_buf(json_data, not noisy)

    print("前回の続きですか？(y/n) ", end="")
    is_continue = input() == "y"
    if is_continue and OneCommeUsers.load_is_first_on_stream():
        print("挨拶キャッシュを復元しました。")

    fs_response = FunctionSkipper(20)

    client = twitchio.Client(
        token=g.config["twitch"]["accessToken"],
        initial_channels=[g.config["twitch"]["loginChannel"]],
    )
    await client.connect()

    bot = TwitchBot()
    await bot.connect()

    fuyukaApi_baseUrl = get_fuyukaApi_baseUrl()
    if fuyukaApi_baseUrl:
        websocket_uri = f"{fuyukaApi_baseUrl}/chat/{g.app_name}"
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
