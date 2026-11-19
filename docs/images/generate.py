"""Generate the README images (banner, card preview light/dark, notification preview).

Run:  python docs/images/generate.py
Icons: Material Design Icons (Apache-2.0), paths in mdi-icons.json.
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

HERE = Path(__file__).parent
ICONS = json.loads((HERE / "mdi-icons.json").read_text())
FONT = "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"

THEMES = {
    "light": dict(page="#eef1f5", card="#ffffff", text="#1f2328", muted="#6b7280", chip="#f1f3f6",
                  input="#f1f3f6", shadow="rgba(16,24,40,.10)", primary="#03a9f4", ontext="#ffffff"),
    "dark": dict(page="#0d1117", card="#1c1f24", text="#e6e8eb", muted="#9aa3ad", chip="#262a31",
                 input="#262a31", shadow="rgba(0,0,0,.45)", primary="#03a9f4", ontext="#ffffff"),
}
BLUE, ORANGE, RED, GREEN = "#2196f3", "#ff9800", "#e5484d", "#43a047"


def icon(name: str, x: float, y: float, size: float, color: str, opacity: float = 1) -> str:
    s = size / 24
    return (f'<g transform="translate({x:.1f},{y:.1f}) scale({s:.4f})" fill="{color}" opacity="{opacity}">'
            f'<path d="{ICONS[name]}"/></g>')


def text(x, y, s, size, color, weight=400, anchor="start") -> str:
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
            f'fill="{color}" text-anchor="{anchor}">{escape(s)}</text>')


def card(theme: str) -> str:
    t = THEMES[theme]
    W, H = 560, 556
    cx, cy, cw, ch = 24, 24, W - 48, H - 48
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<defs><filter id="sh" x="-10%" y="-10%" width="120%" height="130%">'
        f'<feDropShadow dx="0" dy="6" stdDeviation="10" flood-color="{t["shadow"]}"/></filter></defs>',
        f'<rect width="{W}" height="{H}" rx="20" fill="{t["page"]}"/>',
        f'<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="16" fill="{t["card"]}" filter="url(#sh)"/>',
    ]
    L = cx + 20
    R = cx + cw - 20
    # header
    parts.append(text(L, cy + 38, "Parcels", 20, t["text"], 600))
    parts.append(icon("clock-outline", R - 92, cy + 24, 15, t["muted"]))
    parts.append(text(R - 73, cy + 36, "14:32", 13, t["muted"]))
    parts.append(icon("refresh", R - 22, cy + 21, 22, t["muted"]))
    # stats chips
    x = L
    for ic, col, n, label in (("truck-delivery-outline", BLUE, 3, "In transit"), ("storefront-outline", ORANGE, 1, "Ready"),
                              ("alert-circle-outline", RED, 1, "Problems"), ("package-variant-closed-check", GREEN, 2, "Delivered")):
        w = 46 + len(label) * 6.9 + len(str(n)) * 8
        parts.append(f'<rect x="{x}" y="{cy + 56}" width="{w:.0f}" height="32" rx="16" fill="{t["chip"]}"/>')
        parts.append(icon(ic, x + 10, cy + 63, 18, col))
        parts.append(text(x + 33, cy + 77, str(n), 14, t["text"], 700))
        parts.append(text(x + 33 + len(str(n)) * 9 + 4, cy + 77, label, 13, t["muted"]))
        x += w + 8
    # rows
    rows = [
        ("truck-fast-outline", ORANGE, "Headphones", "Out for delivery", "2 hours ago", "Parcel is out for delivery · Frankfurt"),
        ("storefront-outline", ORANGE, "Book", "Ready for pickup", "yesterday", "Ready at Packstation 123 · Berlin"),
        ("truck-delivery-outline", BLUE, "Running shoes", "In transit", "5 hours ago", "Arrived at sorting centre · Leipzig"),
        ("alert-circle-outline", RED, "Phone case", "Problem", "3 days ago", "Address incomplete – contact sender"),
    ]
    y = cy + 108
    for i, (ic, col, name, status, ago, info) in enumerate(rows):
        if i == 0:
            parts.append(f'<rect x="{L - 8}" y="{y - 6}" width="{cw - 24}" height="70" rx="12" fill="{t["chip"]}" opacity=".6"/>')
        parts.append(f'<circle cx="{L + 20}" cy="{y + 28}" r="20" fill="{col}" opacity=".15"/>')
        parts.append(icon(ic, L + 9, y + 17, 22, col))
        parts.append(text(L + 54, y + 16, name, 15, t["text"], 600))
        parts.append(f'<text x="{L + 54}" y="{y + 36}" font-family="{FONT}" font-size="13">'
                     f'<tspan fill="{col}">{escape(status)}</tspan><tspan fill="{t["muted"]}"> · {escape(ago)}</tspan></text>')
        parts.append(text(L + 54, y + 54, info, 12.5, t["muted"]))
        parts.append(icon("open-in-new", R - 18, y + 19, 18, t["muted"]))
        y += 76
    # delivered (collapsed)
    parts.append(icon("chevron-right", L - 2, y + 2, 18, t["muted"]))
    parts.append(text(L + 20, y + 16, "2 delivered", 13, t["muted"]))
    # form
    fy = y + 36
    parts.append(f'<rect x="{L}" y="{fy}" width="170" height="40" rx="10" fill="{t["input"]}"/>')
    parts.append(text(L + 12, fy + 25, "Tracking number", 13, t["muted"]))
    parts.append(f'<rect x="{L + 178}" y="{fy}" width="150" height="40" rx="10" fill="{t["input"]}"/>')
    parts.append(text(L + 190, fy + 25, "Name (optional)", 13, t["muted"]))
    bx = L + 336
    parts.append(f'<rect x="{bx}" y="{fy}" width="{R - bx}" height="40" rx="10" fill="{t["primary"]}"/>')
    parts.append(icon("plus", bx + 14, fy + 10, 20, t["ontext"]))
    parts.append(text(bx + 40, fy + 25, "Add", 14, t["ontext"], 600))
    parts.append("</svg>")
    return "\n".join(parts)


def banner() -> str:
    W, H = 1280, 320
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#0b7bd6"/><stop offset=".55" stop-color="#03a9f4"/><stop offset="1" stop-color="#18c5b6"/>'
        '</linearGradient></defs>',
        f'<rect width="{W}" height="{H}" rx="24" fill="url(#g)"/>',
        # decorative icons
        icon("truck-fast-outline", 930, 40, 230, "#ffffff", .14),
        icon("package-variant-closed", 1110, 170, 130, "#ffffff", .12),
        icon("storefront-outline", 1170, 28, 64, "#ffffff", .10),
        # badge
        '<circle cx="150" cy="160" r="86" fill="#ffffff" opacity=".18"/>',
        icon("package-variant-closed-check", 92, 102, 116, "#ffffff"),
        text(280, 150, "Parcels for 17TRACK", 64, "#ffffff", 700),
        text(282, 198, "Your parcels, beautifully native in Home Assistant", 26, "#ffffff", 400),
    ]
    x = 282
    for label in ("Dashboard card", "Push notifications", "Out-for-delivery detection", "Auto-archive"):
        w = 26 + len(label) * 9.4
        p.append(f'<rect x="{x}" y="226" width="{w:.0f}" height="38" rx="19" fill="#ffffff" opacity=".2"/>')
        p.append(text(x + w / 2, 251, label, 16, "#ffffff", 600, "middle"))
        x += w + 10
    p.append("</svg>")
    return "\n".join(p)


def notifications() -> str:
    W, H = 560, 250
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        f'<rect width="{W}" height="{H}" rx="20" fill="#1b1d22"/>',
    ]
    items = [
        ("🚚 Headphones: Out for delivery", "Parcel is out for delivery · Frankfurt", "now"),
        ("🏪 Book: Ready for pickup", "Ready at Packstation 123 · Berlin", "2 h"),
    ]
    y = 24
    for title, body, when in items:
        p.append(f'<rect x="20" y="{y}" width="{W - 40}" height="92" rx="18" fill="#2b2f36"/>')
        p.append('<circle cx="52" cy="{0}" r="16" fill="#03a9f4"/>'.format(y + 30))
        p.append(icon("home-assistant", 41, y + 19, 22, "#ffffff"))
        p.append(text(78, y + 35, "Home Assistant", 13, "#aeb6c0"))
        p.append(text(W - 40, y + 35, when, 13, "#aeb6c0", 400, "end"))
        p.append(text(40, y + 62, title, 15.5, "#f1f3f5", 600))
        p.append(text(40, y + 82, body, 13.5, "#c3cad3"))
        y += 108
    p.append("</svg>")
    return "\n".join(p)



def brand_icon() -> str:
    """Square brand icon (rendered to custom_components/parcels_17track/brand/*.png)."""
    return "\n".join([
        '<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">',
        '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#0b7bd6"/><stop offset=".55" stop-color="#03a9f4"/><stop offset="1" stop-color="#18c5b6"/>'
        '</linearGradient></defs>',
        '<rect width="512" height="512" rx="112" fill="url(#g)"/>',
        icon("package-variant-closed-check", 86, 86, 340, "#ffffff"),
        "</svg>",
    ])


if __name__ == "__main__":
    (HERE / "banner.svg").write_text(banner(), encoding="utf-8")
    (HERE / "card-light.svg").write_text(card("light"), encoding="utf-8")
    (HERE / "card-dark.svg").write_text(card("dark"), encoding="utf-8")
    (HERE / "notifications.svg").write_text(notifications(), encoding="utf-8")
    (HERE / "brand-icon.svg").write_text(brand_icon(), encoding="utf-8")
    print("written:", ", ".join(sorted(p.name for p in HERE.glob("*.svg"))))
