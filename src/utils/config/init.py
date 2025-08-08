import json 
from src.utils.config.autoresponders import init_autoresponders
from src.utils.config.config import init_config
from src.utils.config.embeds import init_embeds
from src.utils.config.infractions import init_infractions


def init():
    """initializes all databases"""
    init_config()
    init_autoresponders()
    init_embeds()
    init_infractions()

with open("src/utils/config/keys.json", "r") as f:
    allowed_keys = json.load(f)