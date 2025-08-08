import os
import json
from collections import defaultdict

class Localization:
    def __init__(self, default_lang="en"):
        self.default_lang = default_lang
        self.languages = defaultdict(dict)
        self.load_languages()

    def load_languages(self):
        """Load all language files"""
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
        keys = key.split('.')

        current = self.languages.get(lang, {}).get(section, {})
        
        for k in keys:
            if isinstance(current, dict):
                current = current.get(k)
            else:
                current = None
                break

        if current is None and fallback and lang != self.default_lang:
            current = self.languages.get(self.default_lang, {}).get(section, {})
            for k in keys:
                if isinstance(current, dict):
                    current = current.get(k)
                else:
                    current = None
                    break
                
        if isinstance(current, str):
            try:
                return current.format(**kwargs)
            except KeyError:
                return current
        return current

localization = Localization()
supported_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh']