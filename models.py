"""
JSON-based database layer for the numismatic collection.
All reads and writes go through this module.
"""

import json
import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

DB_PATH = Path(__file__).parent / "data" / "collection.json"
DB_DEFAULT_PATH = Path(__file__).parent / "data" / "collection_default.json"

# Hardcoded ruler reign-start years for canonical sort order
RULER_REIGN_START = {
    "Kęstutis":                       1381,
    "Vladimir Olgerdovich":           1362,
    "Jogaila / Władysław II Jagiełło": 1377,
    "Skirgaila":                      1386,
    "Vytautas the Great":             1392,
    "Casimir IV Jagiellon":           1440,
    "Alexander Jagiellon":            1492,
    "Sigismund I the Old":            1506,
    "Sigismund II Augustus":          1544,
    "Gothard Ketler":                 1561,
    "Stephen Báthory":                1576,
    "Sigismund III Vasa":             1587,
    "John II Casimir Vasa":           1648,
}

# Denomination sort order by ascending face value
DENOM_ORDER = {
    "Obol":                  0,
    "Denar":                 1,
    "Double Denar":          2,
    "Half-Grosz (Półgrosz)": 3,
    "Grosz":                 4,
    "Trojak (3 Grosze)":     5,
    "Czworak (4 Grosze)":    6,
    "Szóstak (6 Groszy)":    7,
    "Ort (18 Groszy)":       8,
    "Talar":                 9,
}


def _load() -> dict:
    path = DB_PATH if DB_PATH.exists() else DB_DEFAULT_PATH
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Collection meta
# ---------------------------------------------------------------------------

def get_meta() -> dict:
    meta = _load()["meta"]
    meta.setdefault("show_prices", True)
    meta.setdefault("per_page", 100)
    return meta


def update_meta(name: str, owner: str, show_prices: bool = True,
                per_page: int = 100) -> None:
    data = _load()
    data["meta"]["collection_name"] = name
    data["meta"]["owner"] = owner
    data["meta"]["show_prices"] = show_prices
    data["meta"]["per_page"] = per_page
    _save(data)


# ---------------------------------------------------------------------------
# Ruler notes (editable biographical notes per ruler)
# ---------------------------------------------------------------------------

def get_rulers() -> dict:
    data = _load()
    return data.get("rulers", {})


def update_ruler_notes(ruler_name: str, notes: str) -> None:
    data = _load()
    data.setdefault("rulers", {})
    data["rulers"].setdefault(ruler_name, {})
    data["rulers"][ruler_name]["notes"] = notes
    _save(data)


def get_ruler_seals(ruler_name: str) -> list:
    """Return list of {name, image?} dicts for a ruler."""
    data = _load()
    return data.get("rulers", {}).get(ruler_name, {}).get("seals", [])


def set_ruler_seals(ruler_name: str, seals: list) -> None:
    data = _load()
    data.setdefault("rulers", {})
    data["rulers"].setdefault(ruler_name, {})
    data["rulers"][ruler_name]["seals"] = seals
    _save(data)


def add_ruler_seal(ruler_name: str, name: str) -> int:
    """Append a new seal entry; returns its index."""
    data = _load()
    data.setdefault("rulers", {})
    data["rulers"].setdefault(ruler_name, {})
    seals = data["rulers"][ruler_name].setdefault("seals", [])
    seals.append({"name": name})
    _save(data)
    return len(seals) - 1


def rename_ruler_seal(ruler_name: str, idx: int, name: str) -> bool:
    data = _load()
    seals = data.get("rulers", {}).get(ruler_name, {}).get("seals", [])
    if idx < 0 or idx >= len(seals):
        return False
    seals[idx]["name"] = name
    _save(data)
    return True


def set_ruler_seal_image_db(ruler_name: str, idx: int, filename: str) -> Optional[str]:
    """Set image for a seal; returns old filename if any."""
    data = _load()
    seals = data.get("rulers", {}).get(ruler_name, {}).get("seals", [])
    if idx < 0 or idx >= len(seals):
        return None
    old = seals[idx].get("image")
    seals[idx]["image"] = filename
    _save(data)
    return old


def remove_ruler_seal_image_db(ruler_name: str, idx: int) -> Optional[str]:
    """Remove image from a seal; returns old filename if any."""
    data = _load()
    seals = data.get("rulers", {}).get(ruler_name, {}).get("seals", [])
    if idx < 0 or idx >= len(seals):
        return None
    old = seals[idx].pop("image", None)
    if old is not None:
        _save(data)
    return old


def delete_ruler_seal(ruler_name: str, idx: int) -> Optional[str]:
    """Delete a seal entry entirely; returns its image filename if any."""
    data = _load()
    seals = data.get("rulers", {}).get(ruler_name, {}).get("seals", [])
    if idx < 0 or idx >= len(seals):
        return None
    old_image = seals.pop(idx).get("image")
    _save(data)
    return old_image


# ---------------------------------------------------------------------------
# Coin CRUD
# ---------------------------------------------------------------------------

def get_all_coins() -> list:
    return _load()["coins"]


def get_coin(coin_id: str) -> Optional[dict]:
    for coin in _load()["coins"]:
        if coin["id"] == coin_id:
            return coin
    return None


def create_coin(form_data: dict) -> dict:
    coin = _coin_from_form(form_data)
    coin["id"] = str(uuid.uuid4())
    coin["photos"] = []
    coin["photo_obverse"] = None
    coin["photo_reverse"] = None
    coin["documents"] = []
    coin["created_at"] = datetime.utcnow().isoformat()
    coin["updated_at"] = datetime.utcnow().isoformat()

    data = _load()
    data["coins"].append(coin)
    _save(data)
    return coin


def update_coin(coin_id: str, form_data: dict) -> Optional[dict]:
    data = _load()
    for i, coin in enumerate(data["coins"]):
        if coin["id"] == coin_id:
            updated = _coin_from_form(form_data)
            updated["id"] = coin_id
            updated["photos"] = coin.get("photos", [])
            updated["photo_obverse"] = coin.get("photo_obverse")
            updated["photo_reverse"] = coin.get("photo_reverse")
            updated["documents"] = coin.get("documents", [])
            updated["created_at"] = coin["created_at"]
            updated["updated_at"] = datetime.utcnow().isoformat()
            data["coins"][i] = updated
            _save(data)
            return updated
    return None


def delete_coin(coin_id: str) -> bool:
    data = _load()
    coins = [c for c in data["coins"] if c["id"] != coin_id]
    if len(coins) == len(data["coins"]):
        return False
    data["coins"] = coins
    _save(data)
    return True


def add_photo(coin_id: str, filename: str) -> bool:
    data = _load()
    for coin in data["coins"]:
        if coin["id"] == coin_id:
            coin.setdefault("photos", []).append(filename)
            coin["updated_at"] = datetime.utcnow().isoformat()
            _save(data)
            return True
    return False


def remove_photo(coin_id: str, filename: str) -> bool:
    data = _load()
    for coin in data["coins"]:
        if coin["id"] == coin_id:
            photos = coin.get("photos", [])
            if filename in photos:
                photos.remove(filename)
                # Clear obverse/reverse designation if this photo was tagged
                if coin.get("photo_obverse") == filename:
                    coin["photo_obverse"] = None
                if coin.get("photo_reverse") == filename:
                    coin["photo_reverse"] = None
                coin["updated_at"] = datetime.utcnow().isoformat()
                _save(data)
                return True
    return False


def set_photo_role(coin_id: str, filename: str, role: str) -> bool:
    """Toggle obverse/reverse designation for a photo.
    role: 'obverse' or 'reverse'. Clicking again on the same photo clears it."""
    data = _load()
    for coin in data["coins"]:
        if coin["id"] == coin_id:
            field = "photo_obverse" if role == "obverse" else "photo_reverse"
            if coin.get(field) == filename:
                coin[field] = None          # toggle off
            else:
                coin[field] = filename      # set
            coin["updated_at"] = datetime.utcnow().isoformat()
            _save(data)
            return True
    return False


def add_document(coin_id: str, filename: str, original_name: str) -> bool:
    data = _load()
    for coin in data["coins"]:
        if coin["id"] == coin_id:
            coin.setdefault("documents", []).append({
                "filename": filename,
                "original_name": original_name,
            })
            coin["updated_at"] = datetime.utcnow().isoformat()
            _save(data)
            return True
    return False


def remove_document(coin_id: str, filename: str) -> bool:
    data = _load()
    for coin in data["coins"]:
        if coin["id"] == coin_id:
            docs = coin.get("documents", [])
            new_docs = [d for d in docs if d["filename"] != filename]
            if len(new_docs) < len(docs):
                coin["documents"] = new_docs
                coin["updated_at"] = datetime.utcnow().isoformat()
                _save(data)
                return True
    return False


# ---------------------------------------------------------------------------
# Search / filter / sort
# ---------------------------------------------------------------------------

def search_coins(query: str = "", ruler: str = "", denomination: str = "",
                 material: str = "", tag: str = "", sold: str = "",
                 sort_by: str = "ruler", sort_dir: str = "asc") -> list:
    coins = _load()["coins"]

    q = query.lower().strip()

    def matches(coin):
        if q:
            haystack = " ".join([
                coin.get("ruler", ""),
                coin.get("denomination", ""),
                coin.get("mint", ""),
                coin.get("year_display", ""),
                coin.get("obverse", ""),
                coin.get("reverse", ""),
                coin.get("notes", ""),
                coin.get("provenance", ""),
                " ".join(coin.get("tags", [])),
            ]).lower()
            if q not in haystack:
                return False
        if ruler and coin.get("ruler") != ruler:
            return False
        if denomination and coin.get("denomination") != denomination:
            return False
        if material and coin.get("material") != material:
            return False
        if tag and tag not in coin.get("tags", []):
            return False
        if sold == "yes" and not coin.get("is_sold"):
            return False
        if sold == "no" and coin.get("is_sold"):
            return False
        return True

    filtered = [c for c in coins if matches(c)]

    reverse = sort_dir == "desc"
    def _coin_year(c):
        if c.get("year_from"):
            return int(c["year_from"])
        yd = c.get("year_display") or ""
        for part in yd.replace("–", "-").replace("—", "-").split("-"):
            part = part.strip()
            if part.isdigit() and len(part) == 4:
                return int(part)
        return 9999

    if sort_by == "ruler":
        # Canonical 3-level sort: ruler reign-start → denomination value → coin year
        filtered.sort(
            key=lambda c: (
                RULER_REIGN_START.get(c.get("ruler") or "", 9999),
                DENOM_ORDER.get(c.get("denomination") or "", 999),
                _coin_year(c),
            ),
            reverse=reverse,
        )
    elif sort_by in ("weight", "diameter", "purchase_price", "sale_price"):
        filtered.sort(key=lambda c: float(c.get(sort_by) or 0), reverse=reverse)
    elif sort_by == "year":
        filtered.sort(key=lambda c: _coin_year(c), reverse=reverse)
    else:
        filtered.sort(key=lambda c: c.get(sort_by, "") or "", reverse=reverse)

    return filtered


def get_filter_options() -> dict:
    """Unique values for dropdown filters."""
    coins = _load()["coins"]
    rulers = sorted({c["ruler"] for c in coins if c.get("ruler")})
    denoms = sorted({c["denomination"] for c in coins if c.get("denomination")})
    materials = sorted({c["material"] for c in coins if c.get("material")})
    all_tags = set()
    for c in coins:
        all_tags.update(c.get("tags", []))
    return {
        "rulers": rulers,
        "denominations": denoms,
        "materials": materials,
        "tags": sorted(all_tags),
    }


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _coin_from_form(f: dict) -> dict:
    """Map flat form data to the coin document structure."""
    tags_raw = f.get("tags", "")
    if isinstance(tags_raw, str):
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    else:
        tags = tags_raw

    cat_refs = {}
    for key in ("ivanauskas", "bagdonas", "huletski", "sarankinas", "custom"):
        val = f.get(f"cat_{key}", "").strip()
        if val:
            cat_refs[key] = val

    def _float(key):
        try:
            return float(f.get(key) or 0) or None
        except (ValueError, TypeError):
            return None

    def _int(key):
        try:
            return int(f.get(key) or 0) or None
        except (ValueError, TypeError):
            return None

    return {
        "ruler": f.get("ruler", "").strip(),
        "denomination": f.get("denomination", "").strip(),
        "mint": f.get("mint", "").strip(),
        "year_display": f.get("year_display", "").strip(),
        "year_from": _int("year_from"),
        "year_to": _int("year_to"),
        "material": f.get("material", "").strip(),
        "weight": _float("weight"),
        "diameter": _float("diameter"),
        "condition": f.get("condition", "").strip(),
        "obverse": f.get("obverse", "").strip(),
        "reverse": f.get("reverse", "").strip(),
        "edge": f.get("edge", "").strip(),
        "purchase_price": _float("purchase_price"),
        "purchase_date": f.get("purchase_date", "").strip(),
        "purchase_source": f.get("purchase_source", "").strip(),
        "sale_price": _float("sale_price"),
        "sale_date": f.get("sale_date", "").strip(),
        "is_sold": bool(f.get("is_sold")),
        "catalogue_refs": cat_refs,
        "provenance": f.get("provenance", "").strip(),
        "notes": f.get("notes", "").strip(),
        "tags": tags,
    }
