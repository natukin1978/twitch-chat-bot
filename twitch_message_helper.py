import datetime

import twitchio

from one_comme_users import OneCommeUsers


def create_message_json(msg: twitchio.Message = None) -> dict[str, any]:
    localtime = datetime.datetime.now()
    localtime_iso_8601 = localtime.isoformat()
    json_data = {
        "dateTime": localtime_iso_8601,
        "id": None,
        "displayName": None,
        "nickname": None,
        "content": None,  # 関数外で設定してね
        "isFirst": False,
        "isFirstOnStream": None,  # すぐ下で設定する
        "additionalRequests": None,
    }
    if msg:
        json_data["id"] = msg.author.name
        json_data["displayName"] = msg.author.display_name
        json_data["isFirst"] = msg.first
    OneCommeUsers.update_message_json(json_data)
    return json_data
