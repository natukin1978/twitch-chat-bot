import json

import global_value as g
from one_comme_users import OneCommeUsers
from twitch_message_helper import create_message_json


class Fuyuka:

    @staticmethod
    async def send_message_by_json(json_data: dict[str, any]) -> None:
        if not g.websocket_fuyuka:
            return
        json_str = json.dumps(json_data)
        await g.websocket_fuyuka.send(json_str)

    @staticmethod
    async def send_message_by_json_with_buf(
        json_data: dict[str, any], needs_response: bool
    ) -> None:
        if needs_response:
            g.set_needs_response.add(json_data["dateTime"])
        await Fuyuka.send_message_by_json(json_data)
