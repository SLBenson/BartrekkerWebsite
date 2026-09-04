import os
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

# Configured target languages and targeted base files
LANGUAGES = ['es', 'fr']
FILES_TO_TRANSLATE = ['index.html']

print("Starting automated translation pipeline...")

for lang in LANGUAGES:
    os.makedirs(lang, exist_ok=True)
    print(f"\nProcessing language: {lang.upper()}")
    
    for file_name in FILES_TO_TRANSLATE:
        if not os.path.exists(file_name):
            print(f"  ⚠️ Warning: {file_name} not found. Skipping.")
            continue
            
        with open(file_name, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
        # Parse all elements safely
        for element in soup.find_all(text=True):
            # Skip page headers, structural metadata, scripts, and embedded CSS styling
            if element.parent.name in ['style', 'script', 'head', 'meta', 'link']:
                continue
            # Keep the language selector choices native so they remain clear
            if element.parent.find_parent(class_='footer-lang-switcher'):
                continue
            if not element.strip():
                continue
                
            try:
                translated_text = GoogleTranslator(source='auto', target=lang).translate(element)
                element.replace_with(translated_text)
            except Exception as e:
                print(f"    ❌ Error translating block: {e}")
                
        output_path = os.path.join(lang, file_name)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        print(f"  ✅ Successfully wrote translated file to: {output_path}")

print("\n🎉 Translation pipeline finished cleanly!")
