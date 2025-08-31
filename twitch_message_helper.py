import datetime

import twitchio

from one_comme_users import OneCommeUsers


def create_message_json(
    id: str, displayName: str, isFirst: bool, content: str
) -> dict[str, any]:
    localtime = datetime.datetime.now()
    localtime_iso_8601 = localtime.isoformat()
    json_data = {
        "dateTime": localtime_iso_8601,
        "id": id,
        "displayName": displayName,
        "nickname": None,
        "content": content,
        "isFirst": isFirst,
        "isFirstOnStream": None,  # すぐ下で設定する
        "noisy": False,
        "additionalRequests": None,
    }
    OneCommeUsers.update_message_json(json_data)
    return json_data


def create_message_json(msg: twitchio.Message, content: str) -> dict[str, any]:
    id = msg.author.name
    displayName = msg.author.display_name
    isFirst = msg.first
    return create_message_json(id, displayName, isFirst, content)
