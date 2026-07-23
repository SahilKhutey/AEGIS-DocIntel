'''
AEGIS-MIOS — Text Cleaner
==========================
Clean and normalize layout/parser derived text.
'''

from __future__ import annotations

import re


class TextCleaner:
    '''Normalizes redundant whitespace, tab characters, and multiple newlines.'''

    def clean(self, text: str) -> str:
        '''Cleans whitespace, newlines, and tab characters.'''
        if not text:
            return ''
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        return text.strip()
