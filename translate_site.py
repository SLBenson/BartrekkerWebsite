import os
import re
import json
import time
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup, NavigableString, Comment

LANGUAGES = ['es', 'fr', 'pl', 'it', 'de']
FILES_TO_TRANSLATE = ['index.html', 'blog-post.html']  # remove 'blog-post.html' if you don't want it translated yet
CACHE_FILE = 'translation_cache.json'

# Brand / product names that should never be run through translation.
PROTECTED_TERMS = ['Bartrekker', 'App Store', 'Play Store']

API_KEY = os.environ.get('GOOGLE_TRANSLATE_API_KEY')
if not API_KEY:
    raise SystemExit("❌ GOOGLE_TRANSLATE_API_KEY environment variable not set. Add it as a GitHub Actions secret.")

TRANSLATE_URL = "https://translation.googleapis.com/language/translate/v2"

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        cache = json.load(f)
else:
    cache = {}


def protect(text):
    # Symbol-only placeholder (no letters), so there's nothing word-shaped
    # for the translation engine to "correct" into a made-up word.
    for i, term in enumerate(PROTECTED_TERMS):
        text = re.sub(re.escape(term), f'\u00a7{i}\u00a7', text)
    return text


def restore(text):
    for i, term in enumerate(PROTECTED_TERMS):
        text = text.replace(f'\u00a7{i}\u00a7', term)
    return text


def split_text_into_sentences(text):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def call_translate_api(text, target_lang):
    """Calls the official Google Cloud Translation API (v2, API-key auth)
    using only the standard library — no extra pip packages needed."""
    data = urllib.parse.urlencode({
        'q': text,
        'source': 'en',
        'target': target_lang,
        'format': 'text',
        'key': API_KEY,
    }).encode('utf-8')
    req = urllib.request.Request(TRANSLATE_URL, data=data, method='POST')
    with urllib.request.urlopen(req, timeout=15) as resp:
        payload = json.loads(resp.read().decode('utf-8'))
    return payload['data']['translations'][0]['translatedText']


def translate_text(text, target_lang, retries=3):
    if not text or len(text.strip()) == 0:
        return text

    # If the whole chunk IS a protected term (e.g. "App Store" as its own
    # button label), skip translation entirely instead of sending a bare
    # placeholder through the API — with no surrounding words for context,
    # some languages "correct" it into a made-up word rather than passing
    # it through untouched.
    if text.strip() in PROTECTED_TERMS:
        return text

    key = f"en|{target_lang}|{text}"
    if key in cache:
        return cache[key]

    for attempt in range(retries):
        try:
            translated = restore(call_translate_api(protect(text), target_lang))
            print(f"    ✓ {text[:50]}... → {translated[:50]}...")
            cache[key] = translated
            time.sleep(0.05)  # the official API is far more generous than free scrapers
            return translated
        except Exception as e:
            print(f"    ✗ attempt {attempt + 1} failed: {str(e)[:150]}")
            time.sleep(1.0 * (attempt + 1))

    print(f"    ✗ giving up after {retries} attempts, keeping original: {text[:50]}...")
    cache[key] = text
    return text


EMAIL_RE = re.compile(r'^[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}$')
PHONE_RE = re.compile(r'^\+?[\d\s().-]{6,}$')


def looks_like_contact_info(text):
    """True only for text that IS an email address or phone number, not
    just any text that happens to sit inside a mailto:/tel: link (e.g. a
    "Contact us" button should still get translated)."""
    stripped = text.strip()
    return bool(EMAIL_RE.match(stripped) or PHONE_RE.match(stripped))


def is_skippable(element):
    """Skips <style>/<script>/<head> and the footer language picker itself
    — the language names in the switcher never get run through translation."""
    parent = element.parent if hasattr(element, 'parent') else element
    while parent is not None:
        name = getattr(parent, 'name', None)
        if name in ['style', 'script', 'head', 'noscript']:
            return True
        classes = parent.get('class') if hasattr(parent, 'get') else None
        if classes and 'nav-lang-switcher' in classes:
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
        if looks_like_contact_info(text_content):
            continue  # leave emails/phone numbers exactly as written
        elements_to_translate.append((element, text_content))

    print(f"    Found {len(elements_to_translate)} text elements to translate")

    for element, original_text in elements_to_translate:
        if len(original_text) > 4500:
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
print("Starting automated translation pipeline (Google Cloud Translation API)...")
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
