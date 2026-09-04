import os
import re
import json
from bs4 import BeautifulSoup, NavigableString, Comment
from deep_translator import GoogleTranslator

LANGUAGES = ['es', 'fr']
FILES_TO_TRANSLATE = ['index.html', 'blog-post.html']  # remove 'blog-post.html' if you don't want it translated yet
CACHE_FILE = 'translation_cache.json'

# Brand names that should never be run through translation.
PROTECTED_TERMS = ['Bartrekker']

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        cache = json.load(f)
else:
    cache = {}


def protect(text):
    for i, term in enumerate(PROTECTED_TERMS):
        text = re.sub(re.escape(term), f'%%TERM{i}%%', text)
    return text


def restore(text):
    for i, term in enumerate(PROTECTED_TERMS):
        text = text.replace(f'%%TERM{i}%%', term)
    return text


def split_text_into_sentences(text):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def translate_text(text, target_lang):
    if not text or len(text.strip()) == 0:
        return text
    key = f"en|{target_lang}|{text}"
    if key in cache:
        return cache[key]
    try:
        translated = GoogleTranslator(source='en', target=target_lang).translate(protect(text))
        translated = restore(translated) if translated else text
        print(f"    ✓ {text[:50]}... → {translated[:50]}...")
    except Exception as e:
        print(f"    ✗ Translation error: {str(e)[:100]}")
        translated = text
    cache[key] = translated
    return translated


def is_skippable(element):
    """Skips <style>/<script>/<head>, the footer language picker itself,
    and mailto:/tel: links — so emails, phone numbers and the language
    names in the switcher never get run through translation."""
    parent = element.parent if hasattr(element, 'parent') else element
    while parent is not None:
        name = getattr(parent, 'name', None)
        if name in ['style', 'script', 'head', 'noscript']:
            return True
        classes = parent.get('class') if hasattr(parent, 'get') else None
        if classes and 'footer-lang-switcher' in classes:
            return True
        if name == 'a':
            href = parent.get('href', '') or ''
            if href.startswith('mailto:') or href.startswith('tel:'):
                return True
        parent = getattr(parent, 'parent', None)
    return False


def rewrite_link(value, lang):
    """Makes assets and internal page links work once a page is copied
    into /{lang}/, and keeps internal navigation inside that language."""
    if not value:
        return value
    if re.match(r'^([a-z]+:)?//', value) or value.startswith(('#', 'mailto:', 'tel:', '/')):
        return value  # external, anchor, or already root-relative — leave alone
    fragment = '#' + value.split('#', 1)[1] if '#' in value else ''
    filename = value.split('/')[-1].split('?')[0].split('#')[0]
    if filename in FILES_TO_TRANSLATE:
        return f'/{lang}/{filename}{fragment}'
    return f'/{value}'


def translate_page(soup, target_lang):
    elements_to_translate = []
    for element in soup.find_all(string=True):
        if isinstance(element, Comment) or not isinstance(element, NavigableString):
            continue
        if is_skippable(element):
            continue
        text_content = element.strip()
        if not text_content or len(text_content) < 2:
            continue
        elements_to_translate.append((element, text_content))

    print(f"    Found {len(elements_to_translate)} text elements to translate")

    for element, original_text in elements_to_translate:
        if len(original_text) > 4500:  # deep-translator's practical request limit
            chunks = split_text_into_sentences(original_text)
            translated = " ".join(translate_text(c, target_lang) if len(c) > 2 else c for c in chunks)
        else:
            translated = translate_text(original_text, target_lang)
        element.replace_with(translated)

    for selector, attr in [('meta[name="description"]', 'content'), ('img', 'alt')]:
        for el in soup.select(selector):
            val = el.get(attr)
            if val and val.strip() and not is_skippable(el):
                el[attr] = translate_text(val.strip(), target_lang)

    for tag_name, attr in [('link', 'href'), ('script', 'src'), ('img', 'src'), ('a', 'href')]:
        for el in soup.find_all(tag_name):
            val = el.get(attr)
            if val:
                el[attr] = rewrite_link(val, target_lang)

    if soup.html:
        soup.html['lang'] = target_lang

    return soup


print("=" * 70)
print("Starting automated translation pipeline (deep-translator / Google)...")
print("=" * 70)

for lang in LANGUAGES:
    os.makedirs(lang, exist_ok=True)
    print(f"\n{'=' * 70}\nProcessing language: {lang.upper()}\n{'=' * 70}")

    for file_name in FILES_TO_TRANSLATE:
        if not os.path.exists(file_name):
            print(f"  ⚠️ Warning: {file_name} not found. Skipping.")
            continue

        print(f"\n  Reading {file_name}...")
        with open(file_name, 'r', encoding='utf-8') as f:
            content = f.read()

        soup = BeautifulSoup(content, 'html.parser')
        soup = translate_page(soup, lang)

        output_path = os.path.join(lang, file_name)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        print(f"  ✅ Wrote {output_path}")

with open(CACHE_FILE, 'w', encoding='utf-8') as f:
    json.dump(cache, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 70)
print("🎉 Translation pipeline complete.")
print("=" * 70)
