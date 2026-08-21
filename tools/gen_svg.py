#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère les visuels du README de profil.

Règle de ce script : une seule géométrie, deux palettes. Les variantes claire
et sombre d'un même visuel ne peuvent donc pas diverger — on ne retouche jamais
un SVG à la main, on relance ce fichier :

    python3 tools/gen_svg.py

Aucune police de marque n'est déclarée dans les SVG produits. Un SVG affiché
par GitHub l'est dans une balise <img>, donc en contexte isolé : il ne peut pas
charger JetBrains Mono, Fraunces ou Inter. Déclarer une police jamais servie ne
change rien au rendu et ment sur le fichier — on s'en tient aux piles système.
"""

import io
import os

# --- polices : piles système uniquement, aucune police de marque -----------
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"

# --- palettes : dérivées de la charte GoaCloud -----------------------------
# Les tons d'accent sont assombris sur fond clair (#0f7355, #4b42a8) pour tenir
# le contraste AA ; c'est le rôle de tools/check_contrast.py de le vérifier.
PALETTES = {
    "dark": dict(
        bg="#0a1411", panel="#0e1c18", panel2="#11241d", line="#1d3d34",
        text="#dceae5", muted="#8aa79e", accent="#27c08f", violet="#8a80ee",
    ),
    "light": dict(
        bg="#ffffff", panel="#f4f8f6", panel2="#eef5f2", line="#cfe0d9",
        text="#0a1411", muted="#54736b", accent="#0f7355", violet="#4b42a8",
    ),
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=12, fill="text", weight="400", font=SANS,
         anchor="start", ls=None, p=None, opacity=None):
    a = ' text-anchor="%s"' % anchor if anchor != "start" else ""
    l = ' letter-spacing="%s"' % ls if ls else ""
    o = ' opacity="%s"' % opacity if opacity else ""
    return ('<text x="%s" y="%s" font-family="%s" font-size="%s" font-weight="%s" '
            'fill="%s"%s%s%s>%s</text>' % (x, y, font, size, weight, p[fill], a, l, o, esc(s)))


# ===========================================================================
#  1. Bandeau : une session de terminal
# ===========================================================================

def build_terminal(theme):
    p = PALETTES[theme]
    W, H = 780, 288
    BAR = 38          # hauteur de la barre de titre
    X = 30            # marge de texte
    o = []

    o.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
             'width="%d" height="%d" role="img" aria-labelledby="tt td">' % (W, H, W, H))
    o.append('<title id="tt">antoine@goacloud — session de terminal</title>')
    o.append('<desc id="td">Antoine P., ingénieur cybersécurité, sécurité opérationnelle. '
             'Des outils d\'infrastructure que vous hébergez vous-même : zéro télémétrie, '
             'code auditable, vos données restent chez vous.</desc>')

    # cadre
    o.append('<rect x="0.75" y="0.75" width="%s" height="%s" rx="12" fill="%s" '
             'stroke="%s" stroke-width="1.5"/>' % (W - 1.5, H - 1.5, p["bg"], p["line"]))
    # barre de titre
    o.append('<path d="M0.75 12.75 A12 12 0 0 1 12.75 0.75 L%s 0.75 A12 12 0 0 1 %s 12.75 '
             'L%s %s L0.75 %s Z" fill="%s"/>' % (W - 12.75, W - 0.75, W - 0.75, BAR, BAR, p["panel2"]))
    o.append('<path d="M0.75 %s L%s %s" stroke="%s" stroke-width="1.5"/>' % (BAR, W - 0.75, BAR, p["line"]))
    for i, cx in enumerate((23, 42, 61)):
        fill = p["accent"] if i == 0 else p["line"]
        o.append('<circle cx="%s" cy="19.5" r="4.8" fill="%s"/>' % (cx, fill))
    o.append(text(W / 2, 24, "antoine@goacloud : ~", 12.5, "muted", "500", MONO,
                  anchor="middle", ls="0.6", p=p))

    # --- corps ------------------------------------------------------------
    def prompt(y, cmd):
        return ('<text x="%s" y="%s" font-family="%s" font-size="15.5" font-weight="500">'
                '<tspan fill="%s">$</tspan> <tspan fill="%s">%s</tspan></text>'
                % (X, y, MONO, p["accent"], p["muted"], esc(cmd)))

    o.append(prompt(74, "whoami"))
    o.append(text(X, 119, "Antoine P.", 35, "text", "700", MONO, ls="-0.8", p=p))
    o.append(text(X, 147, "ingénieur cybersécurité · sécurité opérationnelle",
                  16, "accent", "600", MONO, p=p))

    o.append(prompt(187, "cat /etc/motd"))
    o.append(text(X, 212, "Des outils d\'infrastructure que vous hébergez vous-même.",
                  15.5, "text", "400", MONO, p=p))
    o.append(text(X, 234, "Zéro télémétrie, code auditable, vos données restent chez vous.",
                  15.5, "text", "400", MONO, p=p))

    # invite finale + curseur clignotant (SMIL : décoratif, bloc fixe si ignoré)
    o.append('<text x="%s" y="272" font-family="%s" font-size="15.5" font-weight="500" '
             'fill="%s">$</text>' % (X, MONO, p["accent"]))
    o.append('<rect x="%s" y="260" width="9" height="15" rx="1" fill="%s">'
             '<animate attributeName="opacity" values="1;1;0;0" dur="1.15s" '
             'repeatCount="indefinite"/></rect>' % (X + 16, p["accent"]))

    # --- marque : anneau + nuage ------------------------------------------
    o.append(ring_cloud(W - 152, 84, p))

    o.append('</svg>')
    return "\n".join(o) + "\n"


def ring_cloud(x, y, p):
    """L'anneau et le nuage de la marque, 120 px de côté, coin haut-gauche en (x, y)."""
    return (
        '<g transform="translate(%s %s)">'
        '<circle cx="60" cy="60" r="47" fill="none" stroke="%s" stroke-width="6.5"/>'
        '<path d="M27 88 A17 17 0 0 1 30 53.5 A24 24 0 0 1 75 46 '
        'A15.5 15.5 0 0 1 93 88 Z" fill="%s"/>'
        '<path d="M27 88 A17 17 0 0 1 30 53.5 A24 24 0 0 1 75 46 '
        'A15.5 15.5 0 0 1 93 88 Z" fill="none" stroke="%s" stroke-width="3"/>'
        '</g>' % (x, y, p["violet"], p["accent"], p["bg"])
    )


# ===========================================================================
#  2. Specter — une seule variante : le vert de marque tient sur les deux fonds
# ===========================================================================

def build_specter():
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 128" width="120" '
        'height="128" role="img" aria-label="Specter, la mascotte de GoaCloud">\n'
        '  <title>Specter</title>\n'
        '  <defs>\n'
        '    <linearGradient id="specter" x1="0" y1="0" x2="0.4" y2="1">\n'
        '      <stop offset="0" stop-color="#27c08f"/>\n'
        '      <stop offset="1" stop-color="#1D9E75"/>\n'
        '    </linearGradient>\n'
        '  </defs>\n'
        '  <path d="M18,64 A42,44 0 0 1 102,64 L102,100 Q91.5,113 81,100 Q70.5,87 60,100 '
        'Q49.5,113 39,100 Q28.5,87 18,100 Z" fill="url(#specter)"/>\n'
        '  <ellipse cx="45" cy="60" rx="6" ry="8" fill="#0a1411"/>\n'
        '  <ellipse cx="75" cy="60" rx="6" ry="8" fill="#0a1411"/>\n'
        '  <path d="M52,78 Q60,85 68,78" fill="none" stroke="#0a1411" stroke-width="3" '
        'stroke-linecap="round" stroke-opacity="0.75"/>\n'
        '</svg>\n'
    )


# ===========================================================================

def main():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(base, "assets")
    if not os.path.isdir(out):
        os.makedirs(out)
    written = []
    for theme in ("dark", "light"):
        for name, fn in (("terminal", build_terminal),):
            path = os.path.join(out, "%s-%s.svg" % (name, theme))
            with io.open(path, "w", encoding="utf-8") as f:
                f.write(fn(theme))
            written.append(path)
    path = os.path.join(out, "specter.svg")
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(build_specter())
    written.append(path)
    for w in written:
        print(w)


if __name__ == "__main__":
    main()
