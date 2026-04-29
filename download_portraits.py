#!/usr/bin/env python3
"""Download representative portraits of GDL rulers from Wikipedia API."""
import json
import os
import urllib.request
import urllib.parse
from pathlib import Path

PORTRAITS_DIR = Path(__file__).parent / "static" / "portraits"
PORTRAITS_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {'User-Agent': 'NumismaticCollectionApp/1.0 (educational project)'}

# Map app ruler name -> Wikipedia article title
RULERS = [
    ("Kęstutis",                         "Kęstutis"),
    ("Jogaila / Władysław II Jagiełło",  "Jogaila"),
    ("Vytautas the Great",               "Vytautas the Great"),
    ("Švitrigaila",                      "Švitrigaila"),
    ("Casimir IV Jagiellon",             "Casimir IV Jagiellon"),
    ("Alexander Jagiellon",              "Alexander Jagiellon"),
    ("Sigismund I the Old",              "Sigismund I the Old"),
    ("Sigismund II Augustus",            "Sigismund II Augustus"),
    ("Stephen Báthory",                  "Stephen Báthory"),
    ("Sigismund III Vasa",               "Sigismund III Vasa"),
    ("Władysław IV Vasa",                "Władysław IV Vasa"),
    ("John II Casimir Vasa",             "John II Casimir Vasa"),
]

# Safe filename prefix for each ruler
SLUGS = {
    "Kęstutis":                        "kestutis",
    "Jogaila / Władysław II Jagiełło": "jogaila",
    "Vytautas the Great":              "vytautas",
    "Švitrigaila":                     "svitrigaila",
    "Casimir IV Jagiellon":            "casimir_iv",
    "Alexander Jagiellon":             "alexander",
    "Sigismund I the Old":             "sigismund_i",
    "Sigismund II Augustus":           "sigismund_ii",
    "Stephen Báthory":                 "stephen_bathory",
    "Sigismund III Vasa":              "sigismund_iii",
    "Władysław IV Vasa":               "wladyslaw_iv",
    "John II Casimir Vasa":            "john_ii_casimir",
}

results = {}

for ruler_name, wiki_title in RULERS:
    slug = SLUGS[ruler_name]
    # Check if already downloaded
    for ext in ("jpg", "jpeg", "png", "webp"):
        existing = PORTRAITS_DIR / f"portrait_{slug}.{ext}"
        if existing.exists():
            print(f"  SKIP (exists): {ruler_name} -> {existing.name}")
            results[ruler_name] = existing.name
            break
    else:
        # Fetch from Wikipedia API
        api_url = (
            "https://en.wikipedia.org/w/api.php"
            "?action=query"
            "&titles=" + urllib.parse.quote(wiki_title) +
            "&prop=pageimages&pithumbsize=400&format=json&redirects=1"
        )
        try:
            req = urllib.request.Request(api_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read())

            pages = data.get("query", {}).get("pages", {})
            page = next(iter(pages.values()))
            thumb = page.get("thumbnail", {})
            img_url = thumb.get("source", "")

            if img_url:
                # Determine extension
                ext = img_url.split("?")[0].rsplit(".", 1)[-1].lower()
                if ext not in ("jpg", "jpeg", "png", "webp", "gif"):
                    ext = "jpg"
                fname = f"portrait_{slug}.{ext}"
                fpath = PORTRAITS_DIR / fname

                req2 = urllib.request.Request(img_url, headers=HEADERS)
                with urllib.request.urlopen(req2, timeout=20) as img_resp:
                    fpath.write_bytes(img_resp.read())

                results[ruler_name] = fname
                print(f"  OK: {ruler_name} -> {fname}")
            else:
                print(f"  NO IMAGE found for: {ruler_name}")
        except Exception as e:
            print(f"  ERROR {ruler_name}: {e}")

print("\n--- Portrait filename mapping ---")
for k, v in results.items():
    print(f'    "{k}": "{v}",')
