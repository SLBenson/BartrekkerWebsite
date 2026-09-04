import os
import time
import re
from bs4 import BeautifulSoup, NavigableString
import requests

LANGUAGES = ['es', 'fr']
FILES_TO_TRANSLATE = ['index.html']

def split_text_into_sentences(text):
    """Splits text into smaller, safe pieces for translation."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def translate_text(text, target_lang):
    """Translate text using the LibreTranslate API (free, no key required)."""
    try:
        url = "https://libretranslate.de/translate"
        payload = {
            "q": text,
            "source": "en",
            "target": target_lang,
        }
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return result.get("translatedText", text)
        else:
            print(f"    ⚠️ Translation API error: {response.status_code}")
            return text
    except Exception as e:
        print(f"    ⚠️ Translation error: {e}")
        return text

print("Starting automated chunk-safe translation pipeline...")

for lang in LANGUAGES:
    os.makedirs(lang, exist_ok=True)
    print(f"\nProcessing language: {lang.upper()}")
    
    for file_name in FILES_TO_TRANSLATE:
        if not os.path.exists(file_name):
            print(f"  ⚠️ Warning: {file_name} not found. Skipping.")
            continue
            
        with open(file_name, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
        # Extract and update text safely
        for element in soup.find_all(text=True):
            # Skip if not a NavigableString (for safety)
            if not isinstance(element, NavigableString):
                continue
                
            # Skip elements in certain parent tags
            if element.parent.name in ['style', 'script', 'head', 'meta', 'link']:
                continue
            if element.parent.find_parent(class_='footer-lang-switcher'):
                continue
            if not element.strip():
                continue
                
            original_text = element.strip()
            
            # If the block is too long, break it up sentence by sentence
            if len(original_text) > 300:
                chunks = split_text_into_sentences(original_text)
                translated_chunks = []
                
                for chunk in chunks:
                    translated_chunk = translate_text(chunk, lang)
                    if translated_chunk:
                        translated_chunks.append(translated_chunk)
                    else:
                        translated_chunks.append(chunk)
                    time.sleep(0.1)
                
                # Use string replacement instead of replace_with to preserve HTML structure
                translated_text = " ".join(translated_chunks)
                element.replace_with(translated_text)
                
            else:
                # Small text blocks translate normally
                translated_text = translate_text(original_text, lang)
                if translated_text:
                    # Replace the text node with the translated text
                    element.replace_with(translated_text)
                time.sleep(0.05)
                
        output_path = os.path.join(lang, file_name)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(str(soup.prettify()))
            
        print(f"  ✅ Successfully processed: {output_path}")

print("\n🎉 Multilingual engine operation completed successfully!")
