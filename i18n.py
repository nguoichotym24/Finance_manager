import json
from pathlib import Path
import streamlit as st

class Translator:
    def __init__(self):
        self.translations = {}
        self.current_language = 'vi'
        self.load_translations()
    
    def load_translations(self):
        locales_path = Path(__file__).parent / 'locales'
        try:
            for lang_file in locales_path.glob('*.json'):
                lang = lang_file.stem
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations[lang] = json.load(f)
        except Exception as e:
            st.error(f"Lỗi khi tải ngôn ngữ: {str(e)}")
            self.translations = {'vi': {}, 'en': {}}  # Fallback
    
    def set_language(self, language):
        if language in self.translations:
            self.current_language = language
            st.session_state.language = language
    
    def t(self, key, default=None):
        return self.translations.get(self.current_language, {}).get(key, self.translations.get('vi', {}).get(key, default or key)
        )
translator = Translator()