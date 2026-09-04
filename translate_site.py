# translate_site.py
import os
import shutil
from pathlib import Path
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

def translate_html_files(source_dir, target_lang, target_lang_code):
    """Translate HTML files to target language"""
    target_dir = Path(target_lang_code)
    target_dir.mkdir(exist_ok=True)
    
    for html_file in Path(source_dir).glob('*.html'):
        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
        
        # Translate text content
        for string in soup.stripped_strings:
            if string.strip():
                try:
                    translated = GoogleTranslator(source_language='en', target_language=target_lang_code).translate(string)
                    soup.string.replace_with(translated)
                except:
                    pass
        
        # Save translated file
        output_file = target_dir / html_file.name
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(str(soup))

if __name__ == '__main__':
    # Translate to Spanish and French
    translate_html_files('.', 'Spanish', 'es')
    translate_html_files('.', 'French', 'fr')
