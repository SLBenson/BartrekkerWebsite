# Save this file in your root folder as translate_site.py
import os
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

# Target languages (e.g., 'es' for Spanish, 'fr' for French)
LANGUAGES = ['es', 'fr', 'pl']
# Add any files you want translated here
FILES_TO_TRANSLATE = ['index.html']

for lang in LANGUAGES:
    os.makedirs(lang, exist_ok=True)
    
    for file_name in FILES_TO_TRANSLATE:
        if not os.path.exists(file_name):
            continue
            
        with open(file_name, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
        # Safely find text nodes without touching scripts or internal CSS layout rules
        for element in soup.find_all(text=True):
            # STRICTLY skip styling, script elements, metadata, and structural white-spaces
            if element.parent.name in ['style', 'script', 'head', 'meta', 'link']:
                continue
            if not element.strip():
                continue
                
            try:
                # Translate text nodes safely
                translated_text = GoogleTranslator(source='auto', target=lang).translate(element)
                element.replace_with(translated_text)
            except Exception as e:
                print(f"Skipping block due to error: {e}")
                
        # Save the translated combined file into its respective folder
        output_path = os.path.join(lang, file_name)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
print("Translation complete! Your HTML structure and internal CSS styles were preserved successfully.")
