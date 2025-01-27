# Twitch配信チャットBOT

## 概要

このプロジェクトは、Twitchの配信チャットを監視してコメントを返すBOTです。

このソフトウエア単体では配信チャットのコメントに返信できません。
以下のソフトウエアを一緒に使う必要があります。

[電脳娘フユカ (AIモデレーター Fuyuka API)](https://github.com/natukin1978/ai-moderator-fuyuka)

## 重要

このソフトは基本的にノーサポートです。

作者が制御できない、もしくは想像もしていない、不測の事態が起きる可能性が高いです。

このソフトウェアの使用に関して、以下の点をご了承ください:

- 本ソフトウェアの使用により生じた、いかなる損害、障害、トラブルについても、作者は一切の責任を負いません。
- 本ソフトウェアの機能、性能、安全性、信頼性などに関して、いかなる保証も行いません。
- 本ソフトウェアの使用中に発生した、データの消失、破損、不具合などについても、作者は一切の責任を負いません。
- 本ソフトウェアの使用により、第三者の権利を侵害した場合、その責任は全て使用者に帰属します。
- 本ソフトウェアの使用に関する法的責任は、全て使用者に帰属するものとします。

上記の内容をご理解いただき、ご使用ください。
(こちらの内容に納得できない方は使用できません)

たとえ、作者に重大な過失があったとしても、作者は一切の責任を負いません。
本ソフトウェアのご利用は、使用者の責任において行っていただきますようお願いいたします。

考えられる例

- アカウントが凍結される。

## 主な機能

- 配信チャットを監視
- モデレーター APIとのデータの送受信
- チャットにコメントを投稿する

以下はオプション

- Webスクレイピング機能 (URLが含まれる場合、関連情報を返す)
- 音声認識した情報をBOTに渡す(要 ゆかコネNeo)

## 使用方法

1. 各種アカウントの作成
2. Pythonのインストール
3. ソースコード取得
4. 依存ライブラリのインストール
5. 設定
6. 実行

詳しい手順は以下の通りです:

### 1. アカウントの作成

- Twitch

-- 配信チャンネル用
-- BOT用（チャットOAuthトークンも必要）

配信チャンネル用だけでも可。その場合はこちらのチャットOAuthトークンを取得してください。

### 2. Pythonのインストール

Python 3.10以降のバージョンをインストールしてください。

### 3. ソースコード取得

任意の場所に取得します。

取得例
```
git clone https://github.com/natukin1978/twitch-chat-bot.git
```
※ 要 git

### 4. 依存ライブラリのインストール

ライブラリをPipでインストールします。
```
pip install -r requirements.txt
```

※ ライブラリインストール前に`venv`で仮想環境を作成する事をオススメします。

### 5. 設定

#### 基本設定

`config.json.template`を`config.json`にコピーもしくはリネームして設定変更を行います。

必須項目

|キー|内容|
|-|-|
|twitch/loginChannel|チャンネルのユーザー名|
|twitch/accessToken|TwitchチャットOAuthトークン https://twitchapps.com/tmi/|
|fuyukaApi/baseUrl|電脳娘フユカ (AIモデレーター Fuyuka API) |

以下はオプション

|キー|内容|
|-|-|
|phantomJsCloud/apiKey|Webスクレイピング API Key https://phantomjscloud.com/|
|neoInnerApi|ゆかコネNeoの発話の受信(WebSocket,文のみ) https://nmori.github.io/yncneo-Docs/tech/tech_api_neo/#websocket_2|
|oneComme/pathUsersCsv|わんコメのリスナーリストの情報を取り込みます(CSV出力したもの)|

### 6. 実行

実行するには以下のコマンドを実行します。
ただし、先に`電脳娘フユカ (AIモデレーター Fuyuka API)`が動作している必要があります。

```
python twitch_chat_bot.py
```

## 備考

BOTが応答したくないユーザーを指定する事ができます。例えば翻訳アプリのユーザーとか
`exclude_id.txt`というテキストファイルにユーザー名を改行区切りで列挙してください。

例
```
fuyuka_ai
natukiso_translator
```

## 貢献する

このソフトに貢献したい場合は、Issue を開いてアイデアを議論するか、プルリクを送信してください。

ただし、このツールは私の配信のために作ったので、余計な機能は付けませんし、使わない機能は削除します。

## 作者

ナツキソ

- Twitter: [@natukin1978](https://twitter.com/natukin1978)
- Mastodon: [@natukin1978](https://mstdn.jp/@natukin1978)
- Bluesky: [@natukin1978](https://bsky.app/profile/natukin1978.bsky.social)
- Threads: [@natukin1978](https://www.threads.net/@natukin1978)
- GitHub: [@natukin1978](https://github.com/natukin1978)
- Mail: natukin1978@hotmail.com

## ライセンス

Twitch配信チャットBOT は [MIT License](https://opensource.org/licenses/MIT) の下でリリースされました。
