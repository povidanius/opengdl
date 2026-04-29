"""
PDF catalogue generator using ReportLab.
Produces a publication-style catalogue of selected coins.
"""

import io
import os
from pathlib import Path
from typing import Optional
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, PageBreak,
    PageTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)
from reportlab.platypus.flowables import BalancedColumns

UPLOAD_FOLDER   = Path(__file__).parent / "uploads"
PORTRAITS_FOLDER = Path(__file__).parent / "static" / "portraits"
SEALS_FOLDER    = Path(__file__).parent / "static" / "seals"

# ── Unicode font registration ─────────────────────────────────────────────────
_DEJAVU_DIR = Path("/usr/share/fonts/truetype/dejavu")

def _register_fonts():
    pdfmetrics.registerFont(TTFont("DejaVuSans",            _DEJAVU_DIR / "DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Bold",       _DEJAVU_DIR / "DejaVuSans-Bold.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Oblique",    _DEJAVU_DIR / "DejaVuSans-Oblique.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVuSans-BoldOblique",_DEJAVU_DIR / "DejaVuSans-BoldOblique.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVuSerif",           _DEJAVU_DIR / "DejaVuSerif.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVuSerif-Bold",      _DEJAVU_DIR / "DejaVuSerif-Bold.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVuSerif-Italic",    _DEJAVU_DIR / "DejaVuSerif-Italic.ttf"))
    pdfmetrics.registerFontFamily(
        "DejaVuSans",
        normal="DejaVuSans",
        bold="DejaVuSans-Bold",
        italic="DejaVuSans-Oblique",
        boldItalic="DejaVuSans-BoldOblique",
    )
    pdfmetrics.registerFontFamily(
        "DejaVuSerif",
        normal="DejaVuSerif",
        bold="DejaVuSerif-Bold",
        italic="DejaVuSerif-Italic",
        boldItalic="DejaVuSerif-Bold",
    )

_register_fonts()

# ── Colours ──────────────────────────────────────────────────────────────────
GOLD   = colors.HexColor("#B8860B")
DARK   = colors.HexColor("#1a2332")
LIGHT  = colors.HexColor("#f5f0e8")
MID    = colors.HexColor("#e8e0d0")
GREY   = colors.HexColor("#666666")
RULER_BG = colors.HexColor("#f7f3ea")

# ── Styles ────────────────────────────────────────────────────────────────────

def _build_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["title"] = ParagraphStyle(
        "CatTitle",
        fontSize=26, leading=32, textColor=DARK,
        alignment=TA_CENTER, fontName="DejaVuSerif-Bold", spaceAfter=4,
    )
    styles["subtitle"] = ParagraphStyle(
        "CatSubtitle",
        fontSize=13, leading=18, textColor=GOLD,
        alignment=TA_CENTER, fontName="DejaVuSerif-Italic", spaceAfter=2,
    )
    styles["owner"] = ParagraphStyle(
        "CatOwner",
        fontSize=10, leading=14, textColor=GREY,
        alignment=TA_CENTER, fontName="DejaVuSans",
    )
    styles["ruler_name"] = ParagraphStyle(
        "RulerName",
        fontSize=17, leading=22, textColor=DARK,
        fontName="DejaVuSerif-Bold", spaceAfter=3,
    )
    styles["ruler_reign"] = ParagraphStyle(
        "RulerReign",
        fontSize=10, leading=14, textColor=GOLD,
        fontName="DejaVuSans-Bold", spaceAfter=2,
    )
    styles["ruler_dates"] = ParagraphStyle(
        "RulerDates",
        fontSize=9, leading=12, textColor=GREY,
        fontName="DejaVuSans", spaceAfter=4,
    )
    styles["ruler_bio"] = ParagraphStyle(
        "RulerBio",
        fontSize=9, leading=13, textColor=DARK,
        fontName="DejaVuSans", spaceAfter=3,
    )
    styles["ruler_notes"] = ParagraphStyle(
        "RulerNotes",
        fontSize=8.5, leading=12, textColor=GREY,
        fontName="DejaVuSans-Oblique",
    )
    styles["seals_label"] = ParagraphStyle(
        "SealsLabel",
        fontSize=7, leading=9, textColor=GOLD,
        fontName="DejaVuSans-Bold", spaceAfter=2,
    )
    styles["seal_name"] = ParagraphStyle(
        "SealName",
        fontSize=6.5, leading=8, textColor=GREY,
        fontName="DejaVuSans", alignment=TA_CENTER,
    )
    styles["coin_heading"] = ParagraphStyle(
        "CoinHeading",
        fontSize=13, leading=16, textColor=DARK,
        fontName="DejaVuSerif-Bold", spaceBefore=4, spaceAfter=2,
    )
    styles["coin_sub"] = ParagraphStyle(
        "CoinSub",
        fontSize=9, leading=12, textColor=GOLD,
        fontName="DejaVuSans-Oblique", spaceAfter=4,
    )
    styles["label"] = ParagraphStyle(
        "Label",
        fontSize=7, leading=9, textColor=GREY,
        fontName="DejaVuSans-Bold",
    )
    styles["value"] = ParagraphStyle(
        "Value",
        fontSize=9, leading=12, textColor=DARK,
        fontName="DejaVuSans",
    )
    styles["desc"] = ParagraphStyle(
        "Desc",
        fontSize=8.5, leading=12, textColor=colors.black,
        fontName="DejaVuSans", spaceAfter=3,
    )
    styles["cat_ref"] = ParagraphStyle(
        "CatRef",
        fontSize=8, leading=11, textColor=GREY,
        fontName="DejaVuSans-Oblique",
    )
    styles["footer"] = ParagraphStyle(
        "Footer",
        fontSize=7, leading=9, textColor=GREY,
        alignment=TA_CENTER, fontName="DejaVuSans",
    )
    return styles


# ── Page templates ────────────────────────────────────────────────────────────

def _header_footer(canvas, doc, collection_name, owner):
    canvas.saveState()
    w, h = A4

    # Header bar
    canvas.setFillColor(DARK)
    canvas.rect(0, h - 1.4*cm, w, 1.4*cm, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.setFont("DejaVuSerif-Bold", 9)
    canvas.drawCentredString(w/2, h - 0.9*cm, collection_name.upper())

    # Footer
    canvas.setFillColor(GREY)
    canvas.setFont("DejaVuSans", 7)
    canvas.drawString(2*cm, 1*cm, owner)
    canvas.drawCentredString(w/2, 1*cm, "Page %d" % doc.page)
    canvas.drawRightString(w - 2*cm, 1*cm, "Confidential")

    # Gold rule
    canvas.setStrokeColor(GOLD)
    canvas.setLineWidth(0.5)
    canvas.line(2*cm, 1.5*cm, w - 2*cm, 1.5*cm)

    canvas.restoreState()


# ── Ruler section header ──────────────────────────────────────────────────────

def _ruler_block(ruler_name, ruler_info, styles, doc_width):
    """Return flowables for a ruler intro section (portrait + bio)."""
    elements = []

    portrait_fname = ruler_info.get("portrait", "")
    portrait_path = PORTRAITS_FOLDER / portrait_fname if portrait_fname else None

    # Portrait image (if available)
    portrait_img = None
    if portrait_path and portrait_path.exists():
        try:
            img = Image(str(portrait_path))
            iw, ih = img.imageWidth, img.imageHeight
            max_h = 7.15 * cm
            max_w = 5.2 * cm
            ratio = min(max_w / iw, max_h / ih)
            img.drawWidth  = iw * ratio
            img.drawHeight = ih * ratio
            portrait_img = img
        except Exception:
            portrait_img = None

    # Build text column
    text_items = []
    text_items.append(Paragraph(ruler_info.get("full_name", ruler_name), styles["ruler_name"]))
    text_items.append(Paragraph(
        "Reign: " + ruler_info.get("reign", ""),
        styles["ruler_reign"],
    ))
    born  = ruler_info.get("born", "")
    died  = ruler_info.get("died", "")
    if born or died:
        text_items.append(Paragraph(
            ("b. " + born if born else "") +
            ("  ·  d. " + died if died else ""),
            styles["ruler_dates"],
        ))
    bio = ruler_info.get("bio", "")
    if bio:
        text_items.append(Paragraph(bio, styles["ruler_bio"]))
    notes = ruler_info.get("custom_notes", "").strip()
    if notes:
        text_items.append(Spacer(1, 2*mm))
        text_items.append(Paragraph(notes, styles["ruler_notes"]))

    if portrait_img:
        portrait_col_w = 5.5 * cm
        text_col_w = doc_width - portrait_col_w - 4*mm
        tbl = Table(
            [[portrait_img, text_items]],
            colWidths=[portrait_col_w, text_col_w],
        )
        tbl.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        inner = [tbl]
    else:
        inner = text_items

    # Framed ruler section
    frame_tbl = Table([[inner]], colWidths=[doc_width])
    frame_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), RULER_BG),
        ("BOX",           (0, 0), (-1, -1), 1.0, GOLD),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    elements.append(frame_tbl)

    # Seals strip (images with captions, shown below the ruler frame)
    seals = ruler_info.get("seals", [])
    seal_pairs = []
    for s in seals:
        if not s.get("image"):
            continue
        img_path = SEALS_FOLDER / s["image"]
        if not img_path.exists():
            continue
        try:
            img = Image(str(img_path))
            iw, ih = img.imageWidth, img.imageHeight
            max_side = 2.0 * cm
            ratio = min(max_side / iw, max_side / ih)
            img.drawWidth  = iw * ratio
            img.drawHeight = ih * ratio
            seal_pairs.append((img, s["name"]))
        except Exception:
            pass

    if seal_pairs:
        elements.append(Spacer(1, 1.5*mm))
        elements.append(Paragraph("Known Seals", styles["seals_label"]))
        n = len(seal_pairs)
        cell_w = min(2.5 * cm, doc_width / n)
        cells = [[p[0] for p in seal_pairs], [Paragraph(p[1], styles["seal_name"]) for p in seal_pairs]]
        seal_tbl = Table(cells, colWidths=[cell_w] * n)
        seal_tbl.setStyle(TableStyle([
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 2),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 2),
            ("TOPPADDING",    (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]))
        elements.append(seal_tbl)

    elements.append(Spacer(1, 5*mm))
    return elements


# ── Coin card ─────────────────────────────────────────────────────────────────

def _coin_block(coin, styles, doc_width, show_prices=True):
    """Return a list of flowables for one coin entry."""
    elements = []

    # ---- heading ----
    ruler = coin.get("ruler", "Unknown")
    denom = coin.get("denomination", "")
    year  = coin.get("year_display", "")
    heading_text = "%s — %s" % (ruler, denom) + (", %s" % year if year else "")
    elements.append(Paragraph(heading_text, styles["coin_heading"]))

    mint = coin.get("mint", "")
    material = coin.get("material", "")
    sub_parts = [p for p in [mint, material] if p]
    if sub_parts:
        elements.append(Paragraph(" · ".join(sub_parts), styles["coin_sub"]))

    elements.append(HRFlowable(width="100%", thickness=0.4, color=MID, spaceAfter=4))

    # ---- photos ----
    photos = coin.get("photos", [])
    photo_obverse = coin.get("photo_obverse")
    photo_reverse = coin.get("photo_reverse")

    def _load_img(fname, max_side):
        if not fname:
            return None
        fpath = UPLOAD_FOLDER / fname
        if not fpath.exists():
            return None
        try:
            img = Image(str(fpath))
            iw, ih = img.imageWidth, img.imageHeight
            ratio = min(max_side / iw, max_side / ih)
            img.drawWidth = iw * ratio
            img.drawHeight = ih * ratio
            return img
        except Exception:
            return None

    # Obverse / reverse side-by-side with labels
    if photo_obverse or photo_reverse:
        ov_img = _load_img(photo_obverse, 5.5 * cm)
        rv_img = _load_img(photo_reverse, 5.5 * cm)
        col_w = doc_width / 2
        label_row = [
            Paragraph("OBVERSE", styles["label"]),
            Paragraph("REVERSE", styles["label"]),
        ]
        img_row = [
            ov_img if ov_img else Paragraph("—", styles["value"]),
            rv_img if rv_img else Paragraph("—", styles["value"]),
        ]
        tbl = Table([label_row, img_row], colWidths=[col_w, col_w])
        tbl.setStyle(TableStyle([
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND",    (0, 0), (-1, 0),  MID),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("BOX",           (0, 0), (-1, -1), 0.4, MID),
            ("INNERGRID",     (0, 0), (-1, -1), 0.4, MID),
        ]))
        elements.append(tbl)
        elements.append(Spacer(1, 3 * mm))

    # General photos: exclude any already shown as obverse/reverse
    tagged = set(f for f in (photo_obverse, photo_reverse) if f)
    general = [p for p in photos if p not in tagged]
    if general:
        img_cells = []
        for fname in general[:3]:
            img = _load_img(fname, 4.5 * cm)
            if img:
                img_cells.append(img)
        if img_cells:
            while len(img_cells) < 3:
                img_cells.append(Paragraph("", styles["value"]))
            tbl = Table([img_cells], colWidths=[doc_width / 3] * 3)
            tbl.setStyle(TableStyle([
                ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
                ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING",    (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(tbl)
            elements.append(Spacer(1, 3 * mm))

    # ---- spec grid ----
    def spec_cell(label, value):
        return [Paragraph(label, styles["label"]),
                Paragraph(str(value) if value else "—", styles["value"])]

    weight   = ("%s g"   % coin['weight'])   if coin.get("weight")   else "—"
    diameter = ("%s mm"  % coin['diameter']) if coin.get("diameter") else "—"
    condition = coin.get("condition", "—")

    specs = [
        spec_cell("WEIGHT",    weight),
        spec_cell("DIAMETER",  diameter),
        spec_cell("CONDITION", condition),
    ]
    if show_prices:
        purchase = ("EUR %.2f" % coin['purchase_price'] if coin.get("purchase_price") else "—")
        specs.append(spec_cell("PURCHASE", purchase))
        if coin.get("is_sold"):
            sale = ("EUR %.2f" % coin['sale_price'] if coin.get("sale_price") else "—")
            specs.append(spec_cell("SALE PRICE", sale))

    col_w = doc_width / len(specs)
    spec_table = Table([[c[0] for c in specs], [c[1] for c in specs]],
                       colWidths=[col_w] * len(specs))
    spec_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), MID),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("BOX",           (0, 0), (-1, -1), 0.4, MID),
        ("INNERGRID",     (0, 0), (-1, -1), 0.4, MID),
    ]))
    elements.append(spec_table)
    elements.append(Spacer(1, 3*mm))

    # ---- descriptions ----
    obverse = coin.get("obverse", "")
    reverse = coin.get("reverse", "")
    edge    = coin.get("edge", "")

    if obverse:
        elements.append(Paragraph("<b>Obverse:</b> %s" % obverse, styles["desc"]))
    if reverse:
        elements.append(Paragraph("<b>Reverse:</b> %s" % reverse, styles["desc"]))
    if edge:
        elements.append(Paragraph("<b>Edge:</b> %s" % edge, styles["desc"]))

    # ---- catalogue refs ----
    refs = coin.get("catalogue_refs", {})
    if refs:
        ref_labels = {
            "ivanauskas": "Ivanauskas",
            "bagdonas": "Bagdonas",
            "huletski": "Huletski",
            "sarankinas": "Sarankinas",
            "custom": "Ref.",
        }
        ref_str = "  ·  ".join(
            "%s: %s" % (ref_labels.get(k, k), v) for k, v in refs.items() if v
        )
        elements.append(Paragraph(ref_str, styles["cat_ref"]))
        elements.append(Spacer(1, 2*mm))

    # ---- provenance / notes ----
    prov  = coin.get("provenance", "")
    notes = coin.get("notes", "")
    if prov:
        elements.append(Paragraph("<i>Provenance: %s</i>" % prov, styles["cat_ref"]))
    if notes:
        elements.append(Paragraph("<i>Notes: %s</i>" % notes, styles["cat_ref"]))

    # ---- tags ----
    tags = coin.get("tags", [])
    if tags:
        tag_str = "  ".join("[%s]" % t for t in tags)
        elements.append(Spacer(1, 1*mm))
        elements.append(Paragraph(tag_str, styles["cat_ref"]))

    elements.append(Spacer(1, 5*mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=GOLD, spaceAfter=8))

    return [KeepTogether(elements)]


# ── Cover page ────────────────────────────────────────────────────────────────

def _cover_page(collection_name, owner, coin_count, styles):
    elements = []
    elements.append(Spacer(1, 5*cm))

    elements.append(Paragraph(collection_name, styles["title"]))
    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph("Grand Duchy of Lithuania · Numismatic Catalogue", styles["subtitle"]))
    elements.append(Spacer(1, 8*mm))

    if owner:
        elements.append(Paragraph("Collection of %s" % owner, styles["owner"]))
    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph(
        "%d item%s selected" % (coin_count, "s" if coin_count != 1 else ""),
        styles["owner"],
    ))

    elements.append(PageBreak())
    return elements


# ── Public API ────────────────────────────────────────────────────────────────

def generate_pdf(coins, collection_name, owner, show_prices=True,
                 ruler_data=None):
    """Return PDF bytes for the given list of coin dicts.

    ruler_data: dict mapping ruler_name -> {portrait, full_name, reign,
                born, died, bio, custom_notes} (from app.RULER_DATA merged
                with editable DB notes). If None, ruler intro sections are omitted.
    """
    buffer = io.BytesIO()
    styles = _build_styles()

    page_w, page_h = A4
    margin = 2 * cm
    doc_width = page_w - 2 * margin

    def make_page_template(doc):
        frame = Frame(
            margin, 1.8 * cm,
            doc_width, page_h - margin - 1.8 * cm - 1.4 * cm,
            id="main",
        )
        return PageTemplate(
            id="main_tpl",
            frames=[frame],
            onPage=lambda c, d: _header_footer(c, d, collection_name, owner),
        )

    doc = BaseDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=1.4 * cm + 4 * mm,
        bottomMargin=1.8 * cm,
    )
    doc.addPageTemplates([make_page_template(doc)])

    story = _cover_page(collection_name, owner, len(coins), styles)

    if ruler_data:
        # Group coins by ruler, preserving order of first occurrence
        ruler_order = []
        ruler_groups = {}
        for coin in coins:
            rname = coin.get("ruler", "") or "Unknown"
            if rname not in ruler_groups:
                ruler_order.append(rname)
                ruler_groups[rname] = []
            ruler_groups[rname].append(coin)

        for rname in ruler_order:
            # Ruler intro section
            if rname in ruler_data:
                story.extend(_ruler_block(rname, ruler_data[rname], styles, doc_width))
            # Coins for this ruler
            for coin in ruler_groups[rname]:
                story.extend(_coin_block(coin, styles, doc_width, show_prices=show_prices))
    else:
        for coin in coins:
            story.extend(_coin_block(coin, styles, doc_width, show_prices=show_prices))

    doc.build(story)
    return buffer.getvalue()
