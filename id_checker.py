import asyncio
import json
import os
import sys

import twitchio

import global_value as g
from config_helper import read_config, write_config

g.app_name = "id_checker"
g.base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
g.config = read_config()

c_twitch = g.config["twitch"]
if not c_twitch["clientId"] or not c_twitch["clientSecret"]:
    print("失敗: config.json に clientId, clientSecret を書き込んで下さい。")
    sys.exit(1)

print("Botユーザー名:", end="")
bot_name = input()

print("監視チャンネル名:", end="")
owner_name = input()

if not bot_name or not owner_name:
    print("失敗: 未入力の項目がありました。")
    sys.exit(1)


async def main() -> None:
    async with twitchio.Client(
        client_id=c_twitch["clientId"], client_secret=c_twitch["clientSecret"]
    ) as client:
        await client.login()

        try:
            bot_user, owner_user = await client.fetch_users(
                logins=[bot_name, owner_name]
            )
        except Exception as e:
            print(f"失敗: ユーザーの取得に失敗しました。 {e}")
            sys.exit(1)

        c_twitch["botId"] = bot_user.id
        c_twitch["ownerId"] = owner_user.id

        try:
            write_config(data=g.config)

            # 成功時の処理
            print(f"成功: ファイル config.json に書き込みました。")

        except TypeError as e:
            # データにJSON変換できない型（オブジェクトなど）が含まれている場合
            print(f"失敗: JSONに変換できないデータが含まれています。 {e}")

        except OSError as e:
            # 権限不足、ディスク容量不足、無効なパスなど、ファイル操作自体のエラー
            print(f"失敗: ファイルの書き込み中にエラーが発生しました。 {e}")

        except Exception as e:
            # その他の予期せぬエラー
            print(f"失敗: 予期せぬエラーが発生しました。 {e}")


if __name__ == "__main__":
    asyncio.run(main())
