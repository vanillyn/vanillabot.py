import json
import os


class Localization:
    def __init__(self, default_lang="en"):
        self.default_lang = default_lang
        self.languages = {}
        self.load_languages()

    def load_languages(self):
        locales_dir = "locales"
        for filename in os.listdir(locales_dir):
            if filename.endswith(".json"):
                lang_code = filename[:-5]
                with open(
                    os.path.join(locales_dir, filename), "r", encoding="utf-8"
                ) as f:
                    self.languages[lang_code] = json.load(f)

    def get(self, key, lang=None, **kwargs):
        lang = lang or self.default_lang
        data = self.languages.get(lang, {})
        text = data.get(key, self.languages.get(self.default_lang, {}).get(key, key))
        return text.format(**kwargs)


localization = Localization()
