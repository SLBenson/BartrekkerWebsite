import os
import time
import re
from bs4 import BeautifulSoup
from deep_translator import MyMemoryTranslator

LANGUAGES = ['es', 'fr']
FILES_TO_TRANSLATE = ['index.html']

def split_text_into_sentences(text):
    """Splits text into smaller, safe pieces so it never breaks the 500-character API limit."""
    # Split sentences by periods, question marks, or exclamation points while keeping them intact
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

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
            
        translator = MyMemoryTranslator(source='en', target=lang)
            
        # Extract and update text safely
        for element in soup.find_all(text=True):
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
                    try:
                        translated_chunk = translator.translate(chunk)
                        if translated_chunk and not translated_chunk.startswith("MYMEMORY WARNING"):
                            translated_chunks.append(translated_chunk)
                        else:
                            translated_chunks.append(chunk) # Fallback to original text if API errors
                        time.sleep(0.1)
                    except Exception:
                        translated_chunks.append(chunk)
                
                # Combine the translated sentences back together
                element.replace_with(" ".join(translated_chunks))
                
            else:
                # Small text blocks translate normally
                try:
                    translated_text = translator.translate(original_text)
                    if translated_text and not translated_text.startswith("MYMEMORY WARNING"):
                        element.replace_with(translated_text)
                    time.sleep(0.05)
                except Exception as e:
                    print(f"    ❌ Error translating short block: {e}")
                
        output_path = os.path.join(lang, file_name)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        print(f"  ✅ Successfully processed: {output_path}")

print("\n🎉 Multilingual engine operation completed successfully!")
