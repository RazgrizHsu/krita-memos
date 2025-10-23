import locale
import os

_translations = {}
_current_locale = None

def load_translations():
    global _current_locale, _translations

    try:
        system_locale = locale.getdefaultlocale()[0]
        if system_locale and system_locale.startswith('zh'):
            _current_locale = 'zh'
        else:
            _current_locale = 'en'
    except:
        _current_locale = 'en'

    if _current_locale == 'zh':
        trans_file = os.path.join(os.path.dirname(__file__), 'translations', 'zh_TW.py')
        if os.path.exists(trans_file):
            with open(trans_file, 'r', encoding='utf-8') as f:
                exec(f.read(), {'translations': _translations})

def i18n(text):
    if _current_locale == 'zh' and text in _translations:
        return _translations[text]
    return text

load_translations()
