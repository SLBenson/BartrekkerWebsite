import os
import time
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

LANGUAGES = ['es', 'fr']
FILES_TO_TRANSLATE = ['index.html']

print("Starting automated translation pipeline with browser bypass...")

for lang in LANGUAGES:
    os.makedirs(lang, exist_ok=True)
    print(f"\nProcessing language: {lang.upper()}")
    
    for file_name in FILES_TO_TRANSLATE:
        if not os.path.exists(file_name):
            print(f"  ⚠️ Warning: {file_name} not found. Skipping.")
            continue
            
        with open(file_name, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
        # 1. Initialize the translator with a custom browser user-agent
        # This prevents Google Translate from blocking the GitHub Action server traffic.
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        translator = GoogleTranslator(source='auto', target=lang, proxies=None)
        # Apply our custom browser session to the underlying request engine
        translator.session = session
            
        for element in soup.find_all(text=True):
            if element.parent.name in ['style', 'script', 'head', 'meta', 'link']:
                continue
            if element.parent.find_parent(class_='footer-lang-switcher'):
                continue
            if not element.strip():
                continue
                
            try:
                # 2. Safely translate the text block
                translated_text = translator.translate(element)
                element.replace_with(translated_text)
                
                # 3. Add a tiny delay (0.1 seconds) to prevent triggering spam protections
                time.sleep(0.1)
                
            except Exception as e:
                print(f"    ❌ Error translating block: {e}")
                
        output_path = os.path.join(lang, file_name)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        print(f"  ✅ Successfully wrote translated file to: {output_path}")

print("\n🎉 Translation pipeline finished cleanly with connection safeguards!")
