import datetime

import twitchio

from one_comme_users import OneCommeUsers


def create_message_json(
    id: str, display_name: str, is_first: bool, content: str
) -> dict[str, any]:
    localtime = datetime.datetime.now()
    localtime_iso_8601 = localtime.isoformat()
    json_data = {
        "dateTime": localtime_iso_8601,
        "id": id,
        "displayName": display_name,
        "nickname": None,
        "content": content,
        "isFirst": is_first,
        "isFirstOnStream": None,  # すぐ下で設定する
        "noisy": False,
        "additionalRequests": None,
    }
    OneCommeUsers.update_message_json(json_data)
    return json_data


def create_message_json_from_twitchio_message(
    msg: twitchio.Message, content: str
) -> dict[str, any]:
    id = msg.author.name
    display_name = msg.author.display_name
    is_first = msg.first
    return create_message_json(id, display_name, is_first, content)
