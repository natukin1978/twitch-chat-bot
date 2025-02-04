import json

import aiohttp

import global_value as g


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
    async def _get_request(command: str) -> dict[str, any]:
        conf_fa = g.config["fuyukaApi"]
        baseUrl = conf_fa["baseUrl"].replace("ws", "http")
        url = f"{baseUrl}/{command}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                json_data = await response.json()
                return json_data

    @staticmethod
    async def reset_chat() -> bool:
        json_data = await Fuyuka._get_request("reset_chat")
        return json_data["result"]

    @staticmethod
    async def restore() -> bool:
        json_data = await Fuyuka._get_request("restore")
        return json_data["result"]
