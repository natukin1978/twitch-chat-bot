import json
import os

import global_value as g


def read_config(name: str = "config.json"):
    if not os.path.isabs(name):
        name = os.path.join(g.base_dir, name)
    with open(name, "r", encoding="utf-8") as f:
        return json.load(f)


def write_config(data: any, name: str = "config.json"):
    if not os.path.isabs(name):
        name = os.path.join(g.base_dir, name)
    with open(name, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
