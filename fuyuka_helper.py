import aiohttp
import json

import global_value as g
from one_comme_users import OneCommeUsers
from twitch_message_helper import create_message_json


class Fuyuka:

    @staticmethod
    async def send_message_by_json(json_data: dict[str, any]) -> None:
        if not g.websocket_fuyuka_chat:
            return
        json_str = json.dumps(json_data)
        await g.websocket_fuyuka_chat.send(json_str)

    @staticmethod
    async def send_message_by_json_with_buf(
        json_data: dict[str, any], needs_response: bool
    ) -> None:
        if needs_response:
            g.set_needs_response.add(json_data["dateTime"])
        await Fuyuka.send_message_by_json(json_data)

    @staticmethod
    async def flow_story_by_json(json_data: dict[str, any]) -> None:
        if not g.websocket_fuyuka_flow_story:
            return
        json_str = json.dumps(json_data)
        await g.websocket_fuyuka_flow_story.send(json_str)

    @staticmethod
    async def reset_chat() -> bool:
        conf_fa = g.config["fuyukaApi"]
        baseUrl = conf_fa["baseUrl"].replace("ws", "http")
        url = f"{baseUrl}/reset_chat"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                json_data = await response.json()
                return json_data["result"]
