\
\
\
\
\
\
\
\
   

import json
import os


class LanguageManager:
    def __init__(self, default_lang="fa"):
                                  
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.assets_path = os.path.join(base_dir, "assets", "languages.json")
        self.current_lang = default_lang
        self.translations = self._load_translations()
        self._warn_missing()

                                                                               
    def _load_translations(self) -> dict:
        try:
            if os.path.exists(self.assets_path):
                print(f"🔍 Loading languages from: {self.assets_path}")
                with open(self.assets_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            print(f"⚠️  فایل زبان پیدا نشد: {self.assets_path}")
            return {}
        except Exception as e:
            print(f"❌ خطا در بارگذاری زبان‌ها: {e}")
            return {}

    def _warn_missing(self):
\
\
\
           
        en_keys = set(self.translations.get("en", {}).keys())
        for lang, data in self.translations.items():
            if lang == "en":
                continue
            missing = en_keys - set(data.keys())
            if missing:
                print(f"📋 [{lang}] {len(missing)} کلید بدون ترجمه (از en استفاده می‌شود): "
                      f"{', '.join(sorted(missing))}")

                                                                               
    def set_language(self, lang_code: str):
        if lang_code in self.translations:
            self.current_lang = lang_code

    def get(self, key: str, default: str = "") -> str:
\
\
\
           
        lang_data = self.translations.get(self.current_lang, {})
        en_data   = self.translations.get("en", {})
        return lang_data.get(key) or en_data.get(key) or key or default

    def get_supported_languages(self) -> list:
        return list(self.translations.keys())

                                                                               
    def sync_report(self) -> dict:
\
\
\
           
        en_keys = set(self.translations.get("en", {}).keys())
        report = {}
        for lang, data in self.translations.items():
            if lang == "en":
                continue
            report[lang] = sorted(en_keys - set(data.keys()))
        return report

    def export_template(self, output_path: str = None):
\
\
\
           
        report = self.sync_report()
        en_data = self.translations.get("en", {})
        template = {}
        for lang, missing_keys in report.items():
            template[lang] = {k: f"[{lang}] {en_data.get(k, k)}" for k in missing_keys}

        if output_path is None:
            base_dir = os.path.dirname(self.assets_path)
            output_path = os.path.join(base_dir, "missing_translations.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(template, f, ensure_ascii=False, indent=4)
        print(f"✅ قالب ترجمه‌های گم‌شده ذخیره شد: {output_path}")
        return output_path
