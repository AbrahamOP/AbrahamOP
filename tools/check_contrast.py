#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vérifie le contraste des couples texte/fond utilisés dans les SVG générés.

    python3 tools/check_contrast.py

Seuil retenu : 4.5:1 pour le corps de texte, 3:1 pour les textes >= 18.5 px
gras ou >= 24 px (WCAG « large text »).
"""
import sys
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from gen_svg import PALETTES


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def lum(c):
    r, g, b = (lin(x) for x in rgb(c))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# (texte, fond, seuil, libellé)
PAIRS = [
    ("text", "bg", 4.5, "corps sur fond"),
    ("text", "panel", 4.5, "corps sur panneau"),
    ("text", "panel2", 4.5, "corps sur barre de titre"),
    ("muted", "bg", 4.5, "texte secondaire sur fond"),
    ("muted", "panel", 4.5, "texte secondaire sur panneau"),
    ("muted", "panel2", 4.5, "texte secondaire sur barre de titre"),
    ("accent", "bg", 4.5, "accent vert sur fond"),
    ("accent", "panel", 4.5, "accent vert sur panneau"),
    ("accent", "panel2", 4.5, "accent vert sur barre de titre"),
    ("violet", "bg", 4.5, "accent violet sur fond"),
    ("violet", "panel", 4.5, "accent violet sur panneau"),
]


def main():
    fail = 0
    for theme, p in PALETTES.items():
        print("--- palette %s ---" % theme)
        for fg, bg, seuil, label in PAIRS:
            r = ratio(p[fg], p[bg])
            ok = r >= seuil
            fail += 0 if ok else 1
            print("  %-38s %-9s %5.2f:1  %s" % (label, p[fg], r, "OK" if ok else "ECHEC"))
        # fond du SVG contre le fond de page GitHub : simple information
        page = "#0d1117" if theme == "dark" else "#ffffff"
        print("  %-38s %-9s %5.2f:1  (info : le SVG porte son propre fond)"
              % ("fond du SVG vs page GitHub", page, ratio(p["bg"], page)))
    print()
    print("ECHECS : %d" % fail)
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
