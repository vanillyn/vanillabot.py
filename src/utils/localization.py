import os
import json
from collections import defaultdict

class Localization:
    def __init__(self, default_lang="en"):
        self.default_lang = default_lang
        self.languages = defaultdict(dict)
        self.load_languages()

    
    
    def load_languages(self):
        """load all language files"""
        locales_dir = "locales"
        for lang in os.listdir(locales_dir):
            lang_path = os.path.join(locales_dir, lang)
            if os.path.isdir(lang_path):
                for file in os.listdir(lang_path):
                    if file.endswith(".json"):
                        key = file[:-5]
                        with open(os.path.join(lang_path, file), encoding="utf-8") as f:
                            self.languages[lang][key] = json.load(f)

    def get(self, section, key, lang=None, fallback=True, **kwargs):
        """get a localized string"""
        lang = lang or self.default_lang
        entry = self.languages.get(lang, {}).get(section, {}).get(key)
        if not entry and fallback:
            entry = self.languages.get(self.default_lang, {}).get(section, {}).get(key)
        if isinstance(entry, str):
            return entry.format(**kwargs)
        return entry

localization = Localization()
supported_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh']
