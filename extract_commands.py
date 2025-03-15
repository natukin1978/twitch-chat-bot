import re


def extract_commands(text: str) -> list[str]:
    """
    文字列から特定のパターン（/英字, /英字 英数字, /英字 英数字 英数字 ...）を抽出する関数。

    Args:
        text: 抽出元の文字列。

    Returns:
        抽出された文字列のリスト。パターンに一致するものがなければ空のリストを返す。
    """
    pattern = r"/(?P<command>[a-zA-Z]+)(?P<args>(?:\s+[a-zA-Z0-9]+)*)"
    matches = re.finditer(pattern, text)

    result = []
    for match in matches:
        if match.start() == 0 or text[match.start() - 1] != " ":
            result.append(match.group("command"))
            args_str = match.group("args").strip()
            if args_str:
                result.extend(args_str.split())

    return result
