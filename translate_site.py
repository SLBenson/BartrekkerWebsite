import os
import time
from bs4 import BeautifulSoup
from deep_translator import MyMemoryTranslator  # Switched to the unrestricted free engine

LANGUAGES = ['es', 'fr']
FILES_TO_TRANSLATE = ['index.html']

print("Starting automated translation pipeline via open-source engine...")

for lang in LANGUAGES:
    os.makedirs(lang, exist_ok=True)
    print(f"\nProcessing language: {lang.upper()}")
    
    for file_name in FILES_TO_TRANSLATE:
        if not os.path.exists(file_name):
            print(f"  ⚠️ Warning: {file_name} not found. Skipping.")
            continue
            
        with open(file_name, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
        # Initialize the open-source translator
        translator = MyMemoryTranslator(source='en', target=lang)
            
        for element in soup.find_all(text=True):
            if element.parent.name in ['style', 'script', 'head', 'meta', 'link']:
                continue
            if element.parent.find_parent(class_='footer-lang-switcher'):
                continue
            if not element.strip():
                continue
                
            try:
                # Safely request translation text blocks
                translated_text = translator.translate(element)
                
                # Check for rare empty/failed responses from network limits
                if translated_text and not translated_text.startswith("MYMEMORY WARNING"):
                    element.replace_with(translated_text)
                    
                time.sleep(0.05) # Tiny buffer delay
                
            except Exception as e:
                print(f"    ❌ Error translating block: {e}")
                
        output_path = os.path.join(lang, file_name)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        print(f"  ✅ Successfully compiled folder package for: {output_path}")

print("\n🎉 Multilingual engine operation complete!")
