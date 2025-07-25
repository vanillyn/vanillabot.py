import os
import json

config_file = "config.json"

if not os.path.exists(config_file):
    with open(config_file, "w") as f:
        json.dump({}, f)


def load_config():
    with open(config_file, "r") as f:
        return json.load(f)


def save_config(data):
    with open(config_file, "w") as f:
        json.dump(data, f, indent=2)


def get_config_value(guild_id, key):
    data = load_config()
    guild_id = str(guild_id)
    return data.get(guild_id, {}).get(key)


def set_config_value(guild_id, key, value):
    data = load_config()
    guild_id = str(guild_id)
    if guild_id not in data:
        data[guild_id] = {}
    data[guild_id][key] = value
    save_config(data)
