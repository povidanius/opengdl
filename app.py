"""
Numismatic Collection Manager
Flask web application for managing a personal coin collection.
"""

import os
import uuid
from pathlib import Path
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, send_from_directory, jsonify, Response,
)
from werkzeug.utils import secure_filename
from PIL import Image, ImageOps

import models
import pdf_generator

# ── App setup ─────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "numismatics-gdl-secret-2026")
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

@app.context_processor
def inject_asset_version():
    css = Path(__file__).parent / "static" / "css" / "style.css"
    return {"css_v": int(css.stat().st_mtime)}

UPLOAD_FOLDER = Path(__file__).parent / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)
DOCUMENTS_FOLDER = Path(__file__).parent / "uploads" / "documents"
DOCUMENTS_FOLDER.mkdir(parents=True, exist_ok=True)
SEALS_FOLDER = Path(__file__).parent / "static" / "seals"
SEALS_FOLDER.mkdir(parents=True, exist_ok=True)
COATS_FOLDER = Path(__file__).parent / "static" / "coats_of_arms"
COATS_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "tif", "tiff"}
ALLOWED_DOC_EXTENSIONS = {
    "zip", "rar", "7z", "pdf", "doc", "docx", "xls", "xlsx", "txt", "csv",
    "jpg", "jpeg", "png", "gif", "webp", "tif", "tiff",
}
INLINE_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "gif", "webp", "tif", "tiff"}

app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024 * 1024  # 64 MB per file


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def allowed_doc(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_DOC_EXTENSIONS


def _fix_exif_rotation(fpath: Path) -> None:
    """Re-save image with EXIF orientation baked in so all viewers show it upright."""
    try:
        with Image.open(fpath) as img:
            img = ImageOps.exif_transpose(img)
            ext = fpath.suffix.lower()
            if ext in (".jpg", ".jpeg"):
                img.save(fpath, "JPEG", quality=95, subsampling=0)
            elif ext == ".png":
                img.save(fpath, "PNG")
            elif ext in (".tif", ".tiff"):
                img.save(fpath, "TIFF")
            elif ext == ".webp":
                img.save(fpath, "WEBP", quality=95)
            # GIF: skip (may be animated)
    except Exception:
        pass


def _migrate_seal_storage():
    """One-time migration: populate rulers[name].seals list from RULER_DATA + old seal_images."""
    db_rulers = models.get_rulers()
    for rname, rdata in RULER_DATA.items():
        ruler_db = db_rulers.get(rname, {})
        if "seals" not in ruler_db:
            static_seals = rdata.get("seals", [])
            old_images = ruler_db.get("seal_images", {})
            seals = []
            for i, s in enumerate(static_seals):
                entry = {"name": s["name"]}
                img = old_images.get(str(i))
                if img:
                    entry["image"] = img
                seals.append(entry)
            models.set_ruler_seals(rname, seals)


def _prefill_options():
    """Static reference data for dropdowns."""
    rulers = [
        "Mindaugas",
        "Gediminas",
        "Algirdas",
        "Kęstutis",
        "Jogaila / Władysław II Jagiełło",
        "Vladimir Olgerdovich",
        "Vytautas the Great",
        "Skirgaila",

        "Casimir IV Jagiellon",
        "Alexander Jagiellon",
        "Sigismund I the Old",
        "Sigismund II Augustus",
        "Stephen Báthory",
        "Sigismund III Vasa",
        "Władysław IV Vasa",
        "John II Casimir Vasa",
        "Augustus II the Strong",
        "Lietuvos Respublika (1918–1940)",
        "Lietuvos Respublika (from 1990)",
    ]
    denominations = [
        "Obol", "Denar", "Double Denar", "Schilling (Szeląg)",
        "Half-Grosz (Półgrosz)", "Grosz",
        "Trojak (3 Grosze)", "Czworak (4 Grosze)", "Szóstak (6 Groszy)",
        "Ort (Quarter Thaler)", "Półtalar (Half Thaler)", "Talar",
        "Ducat",
    ]
    mints = [
        "Vilnius", "Kaunas", "Other",
    ]
    materials = ["Silver", "Gold", "Billon", "Copper", "Electrum"]
    conditions = [
        "Poor (P-1)", "Fair (F-2)", "About Good (AG-3)",
        "Good (G-4)", "Good (G-6)", "Very Good (VG-8)", "Very Good (VG-10)",
        "Fine (F-12)", "Fine (F-15)",
        "Very Fine (VF-20)", "Very Fine (VF-25)", "Very Fine (VF-30)", "Very Fine (VF-35)",
        "Extremely Fine (EF-40)", "Extremely Fine (EF-45)",
        "About Uncirculated (AU-50)", "About Uncirculated (AU-55)", "About Uncirculated (AU-58)",
        "Mint State (MS-60)", "Mint State (MS-63)", "Mint State (MS-65)", "Mint State (MS-70)",
        "Proof (PR-60)", "Proof (PR-65)", "Proof (PR-70)",
    ]
    return dict(rulers=rulers, denominations=denominations, mints=mints,
                materials=materials, conditions=conditions)


# ── Ruler biographical data (static defaults; notes are editable in DB) ───────

RULER_DATA = {
    "Mindaugas": {
        "portrait": "portrait_mindaugas.jpg",
        "full_name": "Mindaugas (Mindovg)",
        "reign": "c. 1236–1263",
        "born": "c. 1203",
        "died": "1263",
        "bio": (
            "Mindaugas, crowned King of Lithuania in 1253, is traditionally regarded as the ruler who united the Lithuanian lands. His reign marks an important stage in the formation of Lithuanian statehood and its contacts with medieval Europe. No currently known coins can be securely attributed to Mindaugas, but Lithuania’s early monetary tradition is represented by silver ingot money — the Lithuanian “longs” (ilgieji, or kapos)"
        ),
        "seals": [
            {
                "name": "Royal Seal of Mindaugas (c. 1253–1263)",
                "description": "",
            },
        ],
    },
    "Gediminas": {
        "portrait": "portrait_gediminas.jpg",
        "full_name": "Gediminas (Gedimin)",
        "reign": "c. 1316–1341",
        "born": "c. 1275",
        "died": "1341",
        "bio": (
            "Grand Duke of Lithuania and founder of the Gediminid dynasty that would rule "
            "for over two centuries. Built Vilnius as the capital and invited European "
            "craftsmen, merchants, and monks to settle there. Expanded Lithuanian territory "
            "through diplomacy and conquest, incorporating much of modern Belarus. Famous "
            "for his letters to Pope John XXII and Hanseatic cities promoting trade and "
            "religious tolerance."
        ),
        "seals": [
            {
                "name": "Seal of Gediminas (c. 1323)",
                "description": "",
            },
            {
                "name": "Seal with Columns of Gediminas (Gediminaičiai Pillars)",
                "description": "",
            },
        ],
    },
    "Algirdas": {
        "portrait": "portrait_algirdas.jpg",
        "full_name": "Algirdas (Olgierd)",
        "reign": "1345–1377",
        "born": "c. 1296",
        "died": "1377",
        "bio": (
            "Algirdas, Grand Duke of Lithuania from 1345 to 1377, was one of the most powerful rulers of medieval Lithuania. Together with his brother Kęstutis, he secured the Grand Duchy’s position between the Teutonic Order, Muscovy and the lands of Rus’. His reign saw major eastern and southern expansion, making Lithuania one of the largest states in Europe and preparing the ground for the later Jagiellonian dynasty through his son Jogaila"
        ),
        "seals": [
            {
                "name": "Equestrian Seal of Algirdas",
                "description": "",
            },
        ],
    },
    "Kęstutis": {
        "portrait": "portrait_kestutis.jpg",
        "full_name": "Kęstutis of Lithuania",
        "reign": "c. 1381–1382",
        "born": "c. 1297",
        "died": "1382",
        "bio": (
            "Duke of Lithuania, co-ruler with his brother Algirdas. "
            "Renowned for decades of resistance against the Teutonic Knights. "
            "Captured and murdered by his nephew Jogaila."
        ),
        "seals": [
            {
                "name": "Equestrian Seal of Kęstutis",
                "description": "",
            },
        ],
    },
    "Jogaila / Władysław II Jagiełło": {
        "portrait": "portrait_jogaila.jpg",
        "full_name": "Jogaila (Władysław II Jagiełło)",
        "reign": "1377–1401 (GDL); 1386–1434 (Poland)",
        "born": "c. 1352",
        "died": "1434",
        "bio": (
            "Founder of the Jagiellonian dynasty. Converted Lithuania to Christianity "
            "in 1387. Decisive victory at the Battle of Grunwald (1410) against the "
            "Teutonic Order together with Vytautas."
        ),
        "seals": [
            {
                "name": "Grand Ducal Seal of Lithuania (Vytis, c. 1386)",
                "description": "",
            },
            {
                "name": "Great Royal Seal of Poland",
                "description": "",
            },
            {
                "name": "Counter-seal",
                "description": "",
            },
        ],
    },
    "Vladimir Olgerdovich": {
        "portrait": "portrait_vladimir_olgerdovich.jpg",
        "full_name": "Vladimir Olgerdovich",
        "reign": "1362–1394 (Kyiv)",
        "born": "1338",
        "died": "1398",
        "bio": (
            "Son of Algirdas, Grand Duke of Lithuania. Prince of Kyiv from 1362 to 1394, "
            "when he was displaced by Skirgaila. Issued his own coinage — half-grosz pieces "
            "struck at the Kyiv mint, among the earliest coins of the Grand Duchy of Lithuania."
        ),
        "seals": [
            {
                "name": "Dynastic Seal of Vladimir Olgerdovich",
                "description": "",
            },
        ],
    },
    "Vytautas the Great": {
        "portrait": "vytautas_guagnini.jpg",
        "full_name": "Vytautas the Great",
        "reign": "1392–1430",
        "born": "1350",
        "died": "1430",
        "bio": (
            "Lithuania reached its greatest territorial extent under his rule, stretching "
            "from the Baltic to the Black Sea. Led allied forces at Grunwald (1410). "
            "Sought a royal crown but died before coronation."
        ),
        "seals": [
            {
                "name": "Great Seal of Vytautas",
                "description": "",
            },
            {
                "name": "Seal with Columns of Gediminas (Gediminaičiai Pillars)",
                "description": "",
            },
            {
                "name": "Counter-seal",
                "description": "",
            },
        ],
    },
    "Skirgaila": {
        "portrait": "portrait_skirgaila.jpg",
        "full_name": "Skirgaila",
        "reign": "1386–1392",
        "born": "1354",
        "died": "1397",
        "bio": (
            "Son of Algirdas and brother of Jogaila. Appointed Grand Duke's viceroy "
            "in Lithuania after Jogaila became King of Poland. Suppressed Vytautas's "
            "early revolts before eventually yielding power to him."
        ),
        "seals": [
            {
                "name": "Ducal Seal of Skirgaila",
                "description": "",
            },
        ],
    },

    "Casimir IV Jagiellon": {
        "portrait": "portrait_casimir_iv.jpg",
        "full_name": "Casimir IV Jagiellon",
        "reign": "1440–1492",
        "born": "1427",
        "died": "1492",
        "bio": (
            "Casimir IV Jagiellon, Grand Duke of Lithuania from 1440 and King of Poland from 1447, ruled until his death in 1492. During his reign, the Thirteen Years’ War with the Teutonic Order ended with the Second Peace of Toruń in 1466, bringing Royal Prussia under the Polish Crown and reducing the remaining Teutonic state to a Polish fief."
        ),
        "seals": [
            {
                "name": "Great Royal Seal of Poland (Sigillum Maius Regni Poloniae)",
                "description": "",
            },
            {
                "name": "Lithuanian Grand Ducal Equestrian Seal",
                "description": "",
            },
            {
                "name": "Sigillum Secretum (Privy Seal)",
                "description": "",
            },
        ],
    },
    "Alexander Jagiellon": {
        "portrait": "portrait_alexander.jpg",
        "full_name": "Alexander Jagiellon",
        "reign": "1492–1506",
        "born": "1461",
        "died": "1506",
        "bio": (
            "Alexander Jagiellon, Grand Duke of Lithuania from 1492 and King of Poland from 1501, ruled amid Muscovite and Tatar pressure on the Grand Duchy’s frontiers. His reign marked an important step in Lithuanian monetary history: the reform of 1495 introduced a decimal system based on the groat counted as 10 denars and brought Lithuanian coinage closer to contemporary western European monetary standards. Denars and half-groats were struck in Vilnius, while the full groat appeared only later, under Sigismund the Old."
        ),
        "seals": [
            {
                "name": "Great Royal Seal of Poland",
                "description": "",
            },
            {
                "name": "Lithuanian Grand Ducal Seal (Vytis with Double Cross)",
                "description": "",
            },
            {
                "name": "Privy Seal",
                "description": "",
            },
        ],
    },
    "Sigismund I the Old": {
        "portrait": "portrait_sigismund_i.jpg",
        "full_name": "Sigismund I the Old",
        "reign": "1506–1548",
        "born": "1467",
        "died": "1548",
        "bio": (
            "Sigismund I the Old, King of Poland and Grand Duke of Lithuania from 1506 to 1548, was a major Renaissance ruler of the Jagiellonian dynasty. His reign saw cultural flourishing in the Polish-Lithuanian lands and important monetary reforms that brought coinage closer to contemporary European standards. Continuing the reform begun under Alexander Jagiellon, Sigismund’s rule saw dated Lithuanian half-groats from 1509 (1508(?)) and the first Lithuanian groats minted in Vilnius in 1535–1536."
        ),
        "seals": [
            {
                "name": "Great Royal Seal of Poland (Sigillum Maius)",
                "description": "",
            },
            {
                "name": "Grand Ducal Seal of Lithuania",
                "description": "",
            },
            {
                "name": "Sigillum Secretum (Secret Seal)",
                "description": "",
            },
        ],
    },
    "Sigismund II Augustus": {
        "portrait": "portrait_sigismund_ii.jpg",
        "full_name": "Sigismund II Augustus",
        "reign": "1544–1572",
        "born": "1520",
        "died": "1572",
        "bio": (
            "Sigismund II Augustus, the last male Jagiellonian ruler, governed Lithuania from 1544 and ruled as King of Poland and Grand Duke of Lithuania from 1548 to 1572. His reign culminated in the Union of Lublin of 1569, which created the Polish-Lithuanian Commonwealth. A distinguished Renaissance patron and collector, he assembled a celebrated tapestry collection and fostered a refined court culture. In numismatic history, his rule marks one of the richest periods of Lithuanian coinage: the Vilnius mint issued an exceptional variety of denominations, notable not only for their monetary importance but also for their increasingly artful, European-style execution."
        ),
        "seals": [
            {
                "name": "Great Royal Seal (Sigillum Maius Regni Poloniae)",
                "description": "",
            },
            {
                "name": "Lithuanian Grand Ducal Seal with SA Monogram",
                "description": "",
            },
            {
                "name": "Polish Crown Seal with Eagle",
                "description": "",
            },
            {
                "name": "Privy Seal (Sigillum Secretum)",
                "description": "",
            },
        ],
    },
    "Stephen Báthory": {
        "portrait": "portrait_stephen_bathory.jpg",
        "full_name": "Stephen Báthory",
        "reign": "1576–1586",
        "born": "1533",
        "died": "1586",
        "bio": (
            "Stephen Báthory, Prince of Transylvania and elected ruler of the Polish-Lithuanian Commonwealth, reigned as King of Poland and Grand Duke of Lithuania from 1576 to 1586. Renowned as an energetic and capable military commander, he successfully challenged Ivan IV of Muscovy in the final phase of the Livonian War, recovering Polotsk and securing the Commonwealth’s position in Livonia. His reign also left a lasting cultural legacy in Lithuania: in 1579 he granted the privilege establishing the Vilnius Academy, the foundation of today’s Vilnius University."
        ),
        "seals": [
            {
                "name": "Great Royal Seal of Poland",
                "description": "",
            },
            {
                "name": "Lithuanian Grand Ducal Seal (Vytis with Báthory Arms)",
                "description": "",
            },
            {
                "name": "Privy Seal with Báthory Arms",
                "description": "",
            },
        ],
    },
    "Sigismund III Vasa": {
        "portrait": "portrait_sigismund_iii.jpg",
        "full_name": "Sigismund III Vasa",
        "reign": "1587–1632",
        "born": "1566",
        "died": "1632",
        "bio": (
            "Sigismund III Vasa, Grand Duke of Lithuania and King of Poland from 1587 to 1632, was the first Vasa ruler of the Polish-Lithuanian Commonwealth. His reign was shaped in part by dynastic conflict with Sweden and by wars with Muscovy, in which the Grand Duchy of Lithuania played a significant role. In Lithuanian numismatic history, his rule is notable for the continued activity of the Vilnius Mint, which produced a broad range of denominations, including double-denarii, shillings, groats, one-and-a-half-groats, three-groats, and prestigious gold issues of 1, 5, and 10 ducats."
        ),
        "seals": [
            {
                "name": "Great Royal Seal of Poland (Sigillum Maius)",
                "description": "",
            },
            {
                "name": "Grand Ducal Seal of Lithuania",
                "description": "",
            },
            {
                "name": "Equestrian Seal (Cavalier Seal)",
                "description": "",
            },
            {
                "name": "Sigillum Secretum (Privy Seal)",
                "description": "",
            },
        ],
    },
    "Władysław IV Vasa": {
        "portrait": "portrait_wladyslaw_iv.jpg",
        "full_name": "Władysław IV Vasa",
        "reign": "1632–1648",
        "born": "1595",
        "died": "1648",
        "bio": (
            "Son of Sigismund III. Maintained relative peace after the turbulent reign "
            "of his father. Won the Smolensk War against Russia and was renowned as an "
            "enlightened and cultured monarch."
        ),
        "seals": [
            {
                "name": "Great Royal Seal of Poland (Sigillum Maius)",
                "description": "",
            },
            {
                "name": "Grand Ducal Seal of Lithuania",
                "description": "",
            },
            {
                "name": "Privy Seal (Sigillum Secretum)",
                "description": "",
            },
        ],
    },
    "John II Casimir Vasa": {
        "portrait": "portrait_john_ii_casimir.jpg",
        "full_name": "John II Casimir Vasa",
        "reign": "1648–1668",
        "born": "1609",
        "died": "1672",
        "bio": (
            "John II Casimir Vasa, Grand Duke of Lithuania and King of Poland from 1648 to 1668, was the last Vasa ruler of the Polish-Lithuanian Commonwealth. His reign was shaped by major wars with the Cossacks, Muscovy and Sweden. Numismatically, it is notable for the mass issue of copper shillings, the boratynki, struck in large quantities at Vilnius and Kaunas to support wartime finances. He abdicated in 1668."
        ),
        "seals": [
            {
                "name": "Great Royal Seal of Poland (Sigillum Maius)",
                "description": "",
            },
            {
                "name": "Lithuanian Grand Ducal Seal",
                "description": "",
            },
            {
                "name": "Privy Seal (Sigillum Secretum)",
                "description": "",
            },
        ],
    },
    "Augustus II the Strong": {
        "portrait": "portrait_augustus_ii.jpg",
        "full_name": "Augustus II the Strong (Friedrich August I of Saxony)",
        "reign": "1697–1706, 1709–1733",
        "born": "1670",
        "died": "1733",
        "bio": (
            "Augustus II the Strong, Elector of Saxony and King of Poland and Grand Duke "
            "of Lithuania, ruled in two periods: 1697–1706 and 1709–1733. A prominent figure "
            "of the Baroque era, he is remembered for his ambitious political projects, lavish "
            "court in Dresden, and his role in the Great Northern War against Charles XII of "
            "Sweden. His reign brought Saxony's advanced minting technology to the Commonwealth: "
            "Lithuanian coinage of this period includes shillings and groats struck at the "
            "Grodno mint, as well as thalers and tin coinage. Augustus is also famed for "
            "founding the Meissen porcelain manufactory and for his extraordinary art "
            "collections that enriched Dresden's cultural heritage."
        ),
        "seals": [
            {
                "name": "Great Royal Seal of Poland (Sigillum Maius)",
                "description": "",
            },
            {
                "name": "Electoral Seal of Saxony",
                "description": "",
            },
        ],
    },
    "Lietuvos Respublika (1918\u20131940)": {
        "portrait": "portrait_lr_1918.jpg",
        "full_name": "Lietuvos Respublika (1918\u20131940)",
        "reign": "1918\u20131940",
        "born": "",
        "died": "",
        "bio": (
            "The Republic of Lithuania restored its modern statehood on 16 February 1918, when the Council of Lithuania (Lietuvos Taryba) signed the Act of Independence in Vilnius. The interwar republic established its own national currency: the litas, divided into 100 centai, was introduced in 1922. The first Lithuanian coins entered circulation in 1925, with bronze denominations struck at King’s Norton Metal Works in Birmingham and silver denominations at the Royal Mint in London; from 1936, coins were also struck in Kaunas at the Spindulys mint. Designed by Juozas Zikaras, the coins featured national symbols such as the Vytis and the Columns of Gediminas, together with plant and agricultural motifs reflecting the cultural and economic character of the young state. Unfortunatelly, Lithuania’s independent interwar statehood was interrupted by the Soviet occupation of June 1940."
        ),
        "seals": [],
    },
    "Lietuvos Respublika (from 1990)": {
        "portrait": "flag_lithuania.png",
        "full_name": "Lietuvos Respublika (nuo 1990)",
        "reign": "1990\u2013present",
        "born": "",
        "died": "",
        "bio": (
            "The Republic of Lithuania re-established its independence on 11 March 1990, when the Supreme Council of the Republic of Lithuania adopted the Act of the Re-Establishment of the State of Lithuania. The litas returned to circulation on 25 June 1993, replacing the provisional talonas, and was divided into 100 centai. Modern Lithuanian coinage continued the use of national symbols, especially the Vytis and the Columns of Gediminas, while the restored Lithuanian Mint in Vilnius became the main centre for striking Lithuanian circulation and collector coins. In 2015 Lithuania adopted the euro; Lithuanian euro coins bear the Vytis on the national side."
        ),
        "seals": [],
    },
}


_migrate_seal_storage()


# ── Collection overview ────────────────────────────────────────────────────────

@app.route("/")
def index():
    query    = request.args.get("q", "")
    ruler    = request.args.get("ruler", "")
    denom    = request.args.get("denomination", "")
    material = request.args.get("material", "")
    tag      = request.args.get("tag", "")
    sold     = request.args.get("sold", "")
    sort_by  = request.args.get("sort", "ruler")
    sort_dir = request.args.get("dir", "asc")
    page     = max(1, int(request.args.get("page", 1) or 1))

    all_filtered = models.search_coins(query, ruler, denom, material, tag, sold, sort_by, sort_dir)
    meta         = models.get_meta()
    per_page     = meta.get("per_page", 100)

    total_pages = max(1, (len(all_filtered) + per_page - 1) // per_page)
    page        = min(page, total_pages)
    coins       = all_filtered[(page - 1) * per_page : page * per_page]

    filters     = models.get_filter_options()
    total_value = sum(c.get("purchase_price") or 0 for c in models.get_all_coins())

    # Coin counts per ruler for the exposition
    all_coins = models.get_all_coins()
    ruler_counts = {}
    for c in all_coins:
        r = c.get("ruler", "")
        if r:
            ruler_counts[r] = ruler_counts.get(r, 0) + 1

    # Merge static ruler data with editable DB notes; only show rulers with coins
    db_rulers = models.get_rulers()
    ruler_display = {}
    for rname, rdata in RULER_DATA.items():
        if ruler_counts.get(rname, 0) == 0:
            continue
        merged = dict(rdata)
        merged["custom_notes"] = db_rulers.get(rname, {}).get("notes", "")
        ruler_display[rname] = merged

    # Build ruler seals dict for JS
    ruler_seals = {}
    for rname in ruler_display:
        seals_list = models.get_ruler_seals(rname)
        ruler_seals[rname] = [
            {"index": i, "name": s["name"], "image": s.get("image")}
            for i, s in enumerate(seals_list)
        ]

    return render_template(
        "index.html",
        coins=coins,
        filters=filters,
        meta=meta,
        query=query,
        selected_ruler=ruler,
        selected_denom=denom,
        selected_material=material,
        selected_tag=tag,
        selected_sold=sold,
        sort_by=sort_by,
        sort_dir=sort_dir,
        total_count=len(models.get_all_coins()),
        filtered_count=len(all_filtered),
        total_value=total_value,
        page=page,
        total_pages=total_pages,
        per_page=per_page,
        ruler_data=ruler_display,
        ruler_counts=ruler_counts,
        ruler_seals=ruler_seals,
    )


# ── Coin detail ────────────────────────────────────────────────────────────────

@app.route("/coin/<coin_id>")
def coin_detail(coin_id):
    coin = models.get_coin(coin_id)
    if not coin:
        flash("Coin not found.", "error")
        return redirect(url_for("index"))
    return render_template("coin_detail.html", coin=coin, meta=models.get_meta())


# ── Add coin ──────────────────────────────────────────────────────────────────

@app.route("/coin/add", methods=["GET", "POST"])
def coin_add():
    opts = _prefill_options()
    if request.method == "POST":
        coin = models.create_coin(request.form.to_dict())
        flash("Coin added to collection.", "success")
        return redirect(url_for("coin_detail", coin_id=coin["id"]))
    return render_template("coin_form.html", coin=None, opts=opts,
                           meta=models.get_meta(), action="Add")


# ── Edit coin ─────────────────────────────────────────────────────────────────

@app.route("/coin/<coin_id>/edit", methods=["GET", "POST"])
def coin_edit(coin_id):
    coin = models.get_coin(coin_id)
    if not coin:
        flash("Coin not found.", "error")
        return redirect(url_for("index"))

    opts = _prefill_options()
    if request.method == "POST":
        models.update_coin(coin_id, request.form.to_dict())
        flash("Coin updated.", "success")
        return redirect(url_for("coin_detail", coin_id=coin_id))

    return render_template("coin_form.html", coin=coin, opts=opts,
                           meta=models.get_meta(), action="Edit")


# ── Delete coin ───────────────────────────────────────────────────────────────

@app.route("/coin/<coin_id>/delete", methods=["POST"])
def coin_delete(coin_id):
    coin = models.get_coin(coin_id)
    if coin:
        for fname in coin.get("photos", []):
            fpath = UPLOAD_FOLDER / fname
            if fpath.exists():
                fpath.unlink()
        for doc in coin.get("documents", []):
            fpath = DOCUMENTS_FOLDER / doc["filename"]
            if fpath.exists():
                fpath.unlink()
    models.delete_coin(coin_id)
    flash("Coin removed from collection.", "info")
    return redirect(url_for("index"))


# ── Photo upload ──────────────────────────────────────────────────────────────

@app.route("/coin/<coin_id>/upload_photo", methods=["POST"])
def upload_photo(coin_id):
    coin = models.get_coin(coin_id)
    if not coin:
        return jsonify({"error": "Coin not found"}), 404

    files = request.files.getlist("photos")
    saved = []
    for f in files:
        if f and f.filename and allowed_file(f.filename):
            ext = f.filename.rsplit(".", 1)[1].lower()
            fname = f"{coin_id}_{uuid.uuid4().hex[:8]}.{ext}"
            fpath = UPLOAD_FOLDER / fname
            f.save(str(fpath))
            _fix_exif_rotation(fpath)
            models.add_photo(coin_id, fname)
            saved.append(fname)

    if not saved:
        flash("No valid images uploaded. Allowed: jpg, png, gif, webp, tif.", "error")
    else:
        flash(f"{len(saved)} photo(s) uploaded.", "success")

    return redirect(url_for("coin_detail", coin_id=coin_id))


# ── Photo delete ──────────────────────────────────────────────────────────────

@app.route("/coin/<coin_id>/delete_photo/<filename>", methods=["POST"])
def delete_photo(coin_id, filename):
    safe = secure_filename(filename)
    fpath = UPLOAD_FOLDER / safe
    if fpath.exists():
        fpath.unlink()
    models.remove_photo(coin_id, safe)
    flash("Photo removed.", "info")
    return redirect(url_for("coin_detail", coin_id=coin_id))


# ── Set photo role (obverse / reverse) ────────────────────────────────────────

@app.route("/coin/<coin_id>/set_photo_role", methods=["POST"])
def set_photo_role(coin_id):
    filename = secure_filename(request.form.get("filename", ""))
    role = request.form.get("role", "")
    if filename and role in ("obverse", "reverse"):
        models.set_photo_role(coin_id, filename, role)
    return redirect(url_for("coin_detail", coin_id=coin_id))


# ── Document upload ───────────────────────────────────────────────────────────

@app.route("/coin/<coin_id>/upload_document", methods=["POST"])
def upload_document(coin_id):
    coin = models.get_coin(coin_id)
    if not coin:
        flash("Coin not found.", "error")
        return redirect(url_for("index"))

    files = request.files.getlist("documents")
    saved = []
    for f in files:
        if f and f.filename and allowed_doc(f.filename):
            original_name = f.filename
            ext = f.filename.rsplit(".", 1)[1].lower()
            fname = f"{coin_id}_{uuid.uuid4().hex[:8]}.{ext}"
            f.save(str(DOCUMENTS_FOLDER / fname))
            models.add_document(coin_id, fname, original_name)
            saved.append(fname)

    if not saved:
        flash("No valid documents uploaded. Allowed: pdf, images (jpg/png/webp/tif), zip, rar, doc, xls, txt, csv.", "error")
    else:
        flash(f"{len(saved)} document(s) uploaded.", "success")

    return redirect(url_for("coin_detail", coin_id=coin_id))


# ── Document delete ───────────────────────────────────────────────────────────

@app.route("/coin/<coin_id>/delete_document/<filename>", methods=["POST"])
def delete_document(coin_id, filename):
    safe = secure_filename(filename)
    fpath = DOCUMENTS_FOLDER / safe
    if fpath.exists():
        fpath.unlink()
    models.remove_document(coin_id, safe)
    flash("Document removed.", "info")
    return redirect(url_for("coin_detail", coin_id=coin_id))


# ── Document download ─────────────────────────────────────────────────────────

@app.route("/coin/<coin_id>/document/<filename>")
def download_document(coin_id, filename):
    safe = secure_filename(filename)
    coin = models.get_coin(coin_id)
    original_name = safe
    if coin:
        for doc in coin.get("documents", []):
            if doc["filename"] == safe:
                original_name = doc.get("original_name", safe)
                break
    ext = safe.rsplit(".", 1)[-1].lower() if "." in safe else ""
    as_attachment = ext not in INLINE_EXTENSIONS
    return send_from_directory(str(DOCUMENTS_FOLDER), safe,
                               as_attachment=as_attachment,
                               download_name=original_name)


# ── Serve uploads ─────────────────────────────────────────────────────────────

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(str(UPLOAD_FOLDER), filename)


# ── Ruler edit ────────────────────────────────────────────────────────────────

@app.route("/ruler/<path:ruler_name>/edit", methods=["GET", "POST"])
def ruler_edit(ruler_name):
    if ruler_name not in RULER_DATA:
        flash("Issuer not found.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        notes = request.form.get("notes", "").strip()
        models.update_ruler_notes(ruler_name, notes)
        flash(f"Notes for {ruler_name} saved.", "success")
        return redirect(url_for("index"))

    db_rulers = models.get_rulers()
    current_notes = db_rulers.get(ruler_name, {}).get("notes", "")
    static_data = RULER_DATA[ruler_name]
    return render_template(
        "ruler_edit.html",
        ruler_name=ruler_name,
        ruler=static_data,
        current_notes=current_notes,
        seals=models.get_ruler_seals(ruler_name),
        coats_of_arms=models.get_ruler_coats(ruler_name),
        meta=models.get_meta(),
    )


# ── Seal CRUD ─────────────────────────────────────────────────────────────────

@app.route("/ruler/<path:ruler_name>/seal/add", methods=["POST"])
def ruler_seal_add(ruler_name):
    if ruler_name not in RULER_DATA:
        return jsonify({"error": "Issuer not found"}), 404
    name = request.form.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400
    idx = models.add_ruler_seal(ruler_name, name)
    return jsonify({"index": idx, "name": name})


@app.route("/ruler/<path:ruler_name>/seal/<int:seal_idx>/rename", methods=["POST"])
def ruler_seal_rename(ruler_name, seal_idx):
    if ruler_name not in RULER_DATA:
        return jsonify({"error": "Issuer not found"}), 404
    name = request.form.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400
    if not models.rename_ruler_seal(ruler_name, seal_idx, name):
        return jsonify({"error": "Seal not found"}), 404
    return jsonify({"ok": True, "name": name})


@app.route("/ruler/<path:ruler_name>/seal/<int:seal_idx>/upload", methods=["POST"])
def ruler_seal_upload(ruler_name, seal_idx):
    if ruler_name not in RULER_DATA:
        return jsonify({"error": "Issuer not found"}), 404
    seals = models.get_ruler_seals(ruler_name)
    if seal_idx < 0 or seal_idx >= len(seals):
        return jsonify({"error": "Seal index out of range"}), 400
    f = request.files.get("image")
    if not f or not f.filename:
        return jsonify({"error": "No file"}), 400
    if not allowed_file(f.filename):
        return jsonify({"error": "Invalid file type"}), 400
    ext = f.filename.rsplit(".", 1)[1].lower()
    safe_ruler = secure_filename(ruler_name.replace(" ", "_").replace("/", "_"))
    fname = f"seal_{safe_ruler}_{seal_idx}_{uuid.uuid4().hex[:6]}.{ext}"
    fpath = SEALS_FOLDER / fname
    f.save(str(fpath))
    _fix_exif_rotation(fpath)
    old = models.set_ruler_seal_image_db(ruler_name, seal_idx, fname)
    if old:
        old_path = SEALS_FOLDER / old
        if old_path.exists():
            old_path.unlink()
    return jsonify({"filename": fname, "url": f"/static/seals/{fname}"})


@app.route("/ruler/<path:ruler_name>/seal/<int:seal_idx>/delete_image", methods=["POST"])
def ruler_seal_delete_image(ruler_name, seal_idx):
    if ruler_name not in RULER_DATA:
        return jsonify({"error": "Issuer not found"}), 404
    old = models.remove_ruler_seal_image_db(ruler_name, seal_idx)
    if old:
        old_path = SEALS_FOLDER / old
        if old_path.exists():
            old_path.unlink()
    return jsonify({"ok": True})


@app.route("/ruler/<path:ruler_name>/seal/<int:seal_idx>/delete", methods=["POST"])
def ruler_seal_delete(ruler_name, seal_idx):
    if ruler_name not in RULER_DATA:
        return jsonify({"error": "Issuer not found"}), 404
    old_image = models.delete_ruler_seal(ruler_name, seal_idx)
    if old_image:
        old_path = SEALS_FOLDER / old_image
        if old_path.exists():
            old_path.unlink()
    return jsonify({"ok": True})


# ── Coat of Arms CRUD ─────────────────────────────────────────────────────────

@app.route("/ruler/<path:ruler_name>/coat/add", methods=["POST"])
def ruler_coat_add(ruler_name):
    if ruler_name not in RULER_DATA:
        return jsonify({"error": "Issuer not found"}), 404
    name = request.form.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400
    idx = models.add_ruler_coat(ruler_name, name)
    return jsonify({"index": idx, "name": name})


@app.route("/ruler/<path:ruler_name>/coat/<int:coat_idx>/rename", methods=["POST"])
def ruler_coat_rename(ruler_name, coat_idx):
    if ruler_name not in RULER_DATA:
        return jsonify({"error": "Issuer not found"}), 404
    name = request.form.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400
    if not models.rename_ruler_coat(ruler_name, coat_idx, name):
        return jsonify({"error": "Coat of arms not found"}), 404
    return jsonify({"ok": True, "name": name})


@app.route("/ruler/<path:ruler_name>/coat/<int:coat_idx>/upload", methods=["POST"])
def ruler_coat_upload(ruler_name, coat_idx):
    if ruler_name not in RULER_DATA:
        return jsonify({"error": "Issuer not found"}), 404
    coats = models.get_ruler_coats(ruler_name)
    if coat_idx < 0 or coat_idx >= len(coats):
        return jsonify({"error": "Index out of range"}), 400
    f = request.files.get("image")
    if not f or not f.filename:
        return jsonify({"error": "No file"}), 400
    if not allowed_file(f.filename):
        return jsonify({"error": "Invalid file type"}), 400
    ext = f.filename.rsplit(".", 1)[1].lower()
    safe_ruler = secure_filename(ruler_name.replace(" ", "_").replace("/", "_"))
    fname = f"coat_{safe_ruler}_{coat_idx}_{uuid.uuid4().hex[:6]}.{ext}"
    fpath = COATS_FOLDER / fname
    f.save(str(fpath))
    _fix_exif_rotation(fpath)
    old = models.set_ruler_coat_image_db(ruler_name, coat_idx, fname)
    if old:
        old_path = COATS_FOLDER / old
        if old_path.exists():
            old_path.unlink()
    return jsonify({"filename": fname, "url": f"/static/coats_of_arms/{fname}"})


@app.route("/ruler/<path:ruler_name>/coat/<int:coat_idx>/delete_image", methods=["POST"])
def ruler_coat_delete_image(ruler_name, coat_idx):
    if ruler_name not in RULER_DATA:
        return jsonify({"error": "Issuer not found"}), 404
    old = models.remove_ruler_coat_image_db(ruler_name, coat_idx)
    if old:
        old_path = COATS_FOLDER / old
        if old_path.exists():
            old_path.unlink()
    return jsonify({"ok": True})


@app.route("/ruler/<path:ruler_name>/coat/<int:coat_idx>/delete", methods=["POST"])
def ruler_coat_delete(ruler_name, coat_idx):
    if ruler_name not in RULER_DATA:
        return jsonify({"error": "Issuer not found"}), 404
    old_image = models.delete_ruler_coat(ruler_name, coat_idx)
    if old_image:
        old_path = COATS_FOLDER / old_image
        if old_path.exists():
            old_path.unlink()
    return jsonify({"ok": True})


# ── Export ────────────────────────────────────────────────────────────────────

@app.route("/export", methods=["GET"])
def export_page():
    coins = models.search_coins()  # all coins, sorted by ruler/denomination/year
    meta  = models.get_meta()
    return render_template("export.html", coins=coins, meta=meta)


@app.route("/export/pdf", methods=["POST"])
def export_pdf():
    selected_ids = request.form.getlist("coin_ids")
    if not selected_ids:
        flash("Select at least one coin to export.", "error")
        return redirect(url_for("export_page"))

    coins = [models.get_coin(cid) for cid in selected_ids]
    coins = [c for c in coins if c]

    meta = models.get_meta()
    db_rulers = models.get_rulers()

    # Build full ruler info for PDF (static defaults + editable notes + seals)
    ruler_info_for_pdf = {}
    for rname, rdata in RULER_DATA.items():
        merged = dict(rdata)
        merged["custom_notes"] = db_rulers.get(rname, {}).get("notes", "")
        merged["seals"] = models.get_ruler_seals(rname)
        merged["coats_of_arms"] = models.get_ruler_coats(rname)
        ruler_info_for_pdf[rname] = merged

    pdf_bytes = pdf_generator.generate_pdf(
        coins,
        collection_name=meta.get("collection_name", "Numismatic Collection"),
        owner=meta.get("owner", ""),
        show_prices=meta.get("show_prices", True),
        ruler_data=ruler_info_for_pdf,
        confidential=meta.get("confidential", True),
    )

    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="catalogue.pdf"',
            "Content-Length": len(pdf_bytes),
        },
    )


# ── Settings ──────────────────────────────────────────────────────────────────

@app.route("/settings", methods=["GET", "POST"])
def settings():
    meta = models.get_meta()
    if request.method == "POST":
        try:
            per_page = int(request.form.get("per_page", 100) or 100)
            per_page = max(10, min(500, per_page))
        except (ValueError, TypeError):
            per_page = 100
        models.update_meta(
            name=request.form.get("collection_name", "").strip(),
            owner=request.form.get("owner", "").strip(),
            show_prices="show_prices" in request.form,
            per_page=per_page,
            confidential="confidential" in request.form,
        )
        flash("Settings saved.", "success")
        return redirect(url_for("settings"))
    return render_template("settings.html", meta=meta)


# ── JSON API (lightweight) ────────────────────────────────────────────────────

@app.route("/api/coins")
def api_coins():
    return jsonify(models.get_all_coins())


@app.route("/api/coin/<coin_id>")
def api_coin(coin_id):
    coin = models.get_coin(coin_id)
    if not coin:
        return jsonify({"error": "Not found"}), 404
    return jsonify(coin)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
