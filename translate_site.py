import os
import time
import re
from bs4 import BeautifulSoup, NavigableString, Comment
import requests

LANGUAGES = ['es', 'fr']
FILES_TO_TRANSLATE = ['index.html']

def split_text_into_sentences(text):
    """Splits text into smaller, safe pieces for translation."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def translate_text(text, target_lang):
    """Translate text using the LibreTranslate API (free, no key required)."""
    if not text or len(text.strip()) == 0:
        return text
        
    try:
        url = "https://libretranslate.de/translate"
        payload = {
            "q": text,
            "source": "en",
            "target": target_lang,
        }
        response = requests.post(url, json=payload, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            translated = result.get("translatedText", None)
            if translated:
                print(f"      ✓ Translated ({len(text)} chars): {text[:50]}... → {translated[:50]}...")
                return translated
            else:
                print(f"      ✗ No translation returned for: {text[:50]}...")
                return text
        else:
            print(f"      ✗ API error {response.status_code}: {response.text[:100]}")
            return text
    except requests.exceptions.Timeout:
        print(f"      ✗ Translation timeout for: {text[:50]}...")
        return text
    except Exception as e:
        print(f"      ✗ Translation exception: {str(e)[:100]}")
        return text

def test_api(target_lang):
    """Test if the API is working before processing."""
    print(f"  Testing LibreTranslate API for {target_lang}...")
    test_result = translate_text("Hello", target_lang)
    if test_result and test_result != "Hello":
        print(f"  ✅ API test passed: 'Hello' → '{test_result}'")
        return True
    else:
        print(f"  ❌ API test failed: translation did not work")
        return False

print("=" * 70)
print("Starting automated translation pipeline with debugging...")
print("=" * 70)

for lang in LANGUAGES:
    os.makedirs(lang, exist_ok=True)
    print(f"\n{'='*70}")
    print(f"Processing language: {lang.upper()}")
    print(f"{'='*70}")
    
    # Test API first
    if not test_api(lang):
        print(f"⚠️  Skipping {lang} - API is not responding properly")
        continue
    
    for file_name in FILES_TO_TRANSLATE:
        if not os.path.exists(file_name):
            print(f"  ⚠️ Warning: {file_name} not found. Skipping.")
            continue
            
        print(f"\n  Reading {file_name}...")
        with open(file_name, 'r', encoding='utf-8') as f:
            content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
        
        print(f"  Parsing HTML structure...")
        
        # Extract and collect text elements to translate
        elements_to_translate = []
        for element in soup.find_all(text=True):
            # Skip comments
            if isinstance(element, Comment):
                continue
            # Skip if not a NavigableString
            if not isinstance(element, NavigableString):
                continue
            # Skip elements in certain parent tags
            if element.parent.name in ['style', 'script', 'head', 'meta', 'link', 'noscript']:
                continue
            if element.parent.find_parent(class_='footer-lang-switcher'):
                continue
            text_content = element.strip()
            if not text_content or len(text_content) < 2:
                continue
            elements_to_translate.append((element, text_content))
        
        print(f"  Found {len(elements_to_translate)} text elements to translate")
        
        # Now translate the collected elements
        translated_count = 0
        for idx, (element, original_text) in enumerate(elements_to_translate, 1):
            print(f"\n  [{idx}/{len(elements_to_translate)}] Processing: {original_text[:60]}...")
            
            # If the block is too long, break it up sentence by sentence
            if len(original_text) > 300:
                print(f"      (Long text - splitting into sentences)")
                chunks = split_text_into_sentences(original_text)
                translated_chunks = []
                
                for chunk in chunks:
                    if len(chunk.strip()) > 2:
                        translated_chunk = translate_text(chunk, lang)
                        translated_chunks.append(translated_chunk)
                    else:
                        translated_chunks.append(chunk)
                    time.sleep(0.2)
                
                translated_text = " ".join(translated_chunks)
                element.replace_with(translated_text)
                translated_count += 1
                
            else:
                # Small text blocks translate normally
                translated_text = translate_text(original_text, lang)
                if translated_text != original_text:
                    element.replace_with(translated_text)
                    translated_count += 1
                else:
                    print(f"      (Translation failed or unchanged, keeping original)")
                time.sleep(0.2)
        
        output_path = os.path.join(lang, file_name)
        # Write using str() to preserve original formatting
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        print(f"\n  ✅ Successfully processed: {output_path}")
        print(f"     Total text elements translated: {translated_count}/{len(elements_to_translate)}")

print("\n" + "=" * 70)
print("🎉 Multilingual engine operation completed!")
print("=" * 70)
