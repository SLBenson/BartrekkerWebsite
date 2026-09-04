import os
import time
import re
from bs4 import BeautifulSoup, NavigableString, Comment
from google.cloud import translate_v2
import google.auth

LANGUAGES = ['es', 'fr']
FILES_TO_TRANSLATE = ['index.html']

# Initialize Google Cloud Translation client
try:
    credentials, project = google.auth.default()
    translate_client = translate_v2.Client(credentials=credentials)
except Exception as e:
    print(f"⚠️ Could not initialize Google Cloud Translation: {e}")
    print("Falling back to googletrans library...")
    from googletrans import Translator
    fallback_translator = Translator()
    translate_client = None

def split_text_into_sentences(text):
    """Splits text into smaller, safe pieces for translation."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def translate_text(text, target_lang):
    """Translate text using Google Cloud Translation or googletrans as fallback."""
    if not text or len(text.strip()) == 0:
        return text
        
    try:
        if translate_client:
            # Use Google Cloud Translation
            result = translate_client.translate_text(
                text,
                source_language='en',
                target_language=target_lang
            )
            translated = result['translatedText']
        else:
            # Use googletrans as fallback
            result = fallback_translator.translate(text, src_lang='en', dest_lang=target_lang)
            translated = result.text
        
        if translated and translated != text:
            print(f"      ✓ Translated: {text[:50]}... → {translated[:50]}...")
            return translated
        else:
            print(f"      ✗ Translation returned same text: {text[:50]}...")
            return text
    except Exception as e:
        print(f"      ✗ Translation error: {str(e)[:100]}")
        return text

def test_api(target_lang):
    """Test if translation is working before processing."""
    print(f"  Testing translation API for {target_lang}...")
    test_result = translate_text("Hello world", target_lang)
    if test_result and test_result.lower() != "hello world":
        print(f"  ✅ API test passed: 'Hello world' → '{test_result}'")
        return True
    else:
        print(f"  ❌ API test failed: translation did not work")
        return False

print("=" * 70)
print("Starting automated translation pipeline with Google Translate...")
print("=" * 70)

for lang in LANGUAGES:
    os.makedirs(lang, exist_ok=True)
    print(f"\n{'='*70}")
    print(f"Processing language: {lang.upper()}")
    print(f"{'='*70}")
    
    # Test API first
    if not test_api(lang):
        print(f"⚠️  Skipping {lang} - Translation API is not responding")
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
                    time.sleep(0.1)
                
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
                    print(f"      (Translation unchanged, keeping original)")
                time.sleep(0.1)
        
        output_path = os.path.join(lang, file_name)
        # Write using str() to preserve original formatting
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        print(f"\n  ✅ Successfully processed: {output_path}")
        print(f"     Total text elements translated: {translated_count}/{len(elements_to_translate)}")

print("\n" + "=" * 70)
print("🎉 Multilingual engine operation completed!")
print("=" * 70)
