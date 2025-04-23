import json
from pathlib import Path
import streamlit as st

class Translator:
    def __init__(self):
        self.translations = {}
        self.current_language = 'vi'  # Default language
        self.load_translations()
    
    def load_translations(self):
        locales_path = Path(__file__).parent / "locales"
        try:
            for lang_file in locales_path.glob("*.json"):
                lang = lang_file.stem
                with open(lang_file, "r", encoding="utf-8") as f:
                    self.translations[lang] = json.load(f)
        except Exception as e:
            st.error(f"Translation load error: {str(e)}")
            self.translations = {'vi': {}, 'en': {}}  # Fallback

    def set_language(self, language: str):
        if language in self.translations:
            self.current_language = language
        else:
            st.error(f"Language {language} not supported")

    def t(self, key: str, **kwargs) -> str:
        translation = self.translations.get(self.current_language, {}).get(key, key)
        return translation.format(**kwargs) if kwargs else translation

translator = Translator()