#!/usr/bin/env python3
"""
Regenerates sitemap.xml from a fixed list of top-level pages plus every
entry in blog/posts.json. Runs automatically on every push via
.github/workflows/static.yml — nothing needs to be updated by hand when
you publish a new blog post. Only edit FIXED_PAGES below if you add a
brand new top-level page to the site (not a blog post).
"""
import json
import os
from datetime import datetime, timezone
from xml.sax.saxutils import escape

DOMAIN = "https://bartrekker.com"
POSTS_JSON = "blog/posts.json"
OUTPUT_FILE = "sitemap.xml"

# Add any new top-level pages here manually.
FIXED_PAGES = [
    {"path": "/", "priority": "1.0"},
    {"path": "/blog/", "priority": "0.7"},
    {"path": "/terms-and-conditions/", "priority": "0.8"},
    {"path": "/privacypolicy/", "priority": "0.8"},
    {"path": "/accountdeletion/", "priority": "0.8"},
]

BLOG_POST_PRIORITY = "0.6"


def load_posts():
    if not os.path.exists(POSTS_JSON):
        print(f"⚠️  {POSTS_JSON} not found — sitemap will only include fixed pages.")
        return []
    with open(POSTS_JSON, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print(f"⚠️  Could not parse {POSTS_JSON} ({e}). Skipping blog posts in sitemap.")
            return []


def to_iso(date_str, fallback):
    """Converts a plain YYYY-MM-DD date into a full ISO 8601 timestamp."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    except (ValueError, TypeError):
        return fallback


def main():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    posts = load_posts()

    entries = []
    for page in FIXED_PAGES:
        entries.append({
            "loc": f"{DOMAIN}{page['path']}",
            "lastmod": now,
            "priority": page["priority"],
        })

    for post in posts:
        url = post.get("url", "")
        if not url:
            continue
        if not url.startswith("/"):
            url = "/" + url
        entries.append({
            "loc": f"{DOMAIN}{url}",
            "lastmod": to_iso(post.get("date"), now),
            "priority": BLOG_POST_PRIORITY,
        })

    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for entry in entries:
        lines.append("  <url>")
        lines.append(f"    <loc>{escape(entry['loc'])}</loc>")
        lines.append(f"    <lastmod>{entry['lastmod']}</lastmod>")
        lines.append(f"    <priority>{entry['priority']}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"✅ Wrote {OUTPUT_FILE} with {len(entries)} URLs "
          f"({len(FIXED_PAGES)} fixed pages + {len(posts)} blog posts).")


if __name__ == "__main__":
    main()
