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
#  2. Schéma : la segmentation du banc d'essai
# ===========================================================================

ROWS = [
    ("VLAN 10", "", "DMZ",
     "ce qui est joignable depuis l'extérieur, et rien d'autre", "exposé", "violet"),
    ("VLAN 20", "", "Services",
     "Traefik en TLS wildcard, Docker, GoaCore, applications", "cœur applicatif", "accent"),
    ("VLAN 30", "", "Sécurité",
     "SIEM Wazuh, collecte des journaux, outils offensifs", "observation", "violet"),
    ("VLAN 40", "", "Management",
     "hyperviseur Proxmox, sauvegardes, administration", "accès restreint", "accent"),
    ("VLAN 50", "", "Formation",
     "travaux pratiques, machines montées puis détruites", "éphémère", "accent"),
    ("VLAN 60", "", "Laboratoire",
     "environnement de test cloisonné, sans route sortante", "cloisonné", "violet"),
]


def arrow_down(x, y0, y1, color):
    return ('<path d="M%s %s L%s %s" stroke="%s" stroke-width="1.4" fill="none"/>'
            '<path d="M%s %s L%s %s L%s %s Z" fill="%s"/>'
            % (x, y0, x, y1 - 7, color, x - 4.5, y1 - 7.5, x + 4.5, y1 - 7.5, x, y1, color))


def arrow_right(x0, x1, y, color, dash=None):
    d = ' stroke-dasharray="%s"' % dash if dash else ""
    return ('<path d="M%s %s L%s %s" stroke="%s" stroke-width="1.4" fill="none"%s/>'
            '<path d="M%s %s L%s %s L%s %s Z" fill="%s"/>'
            % (x0, y, x1 - 7, y, color, d, x1 - 7.5, y - 4.5, x1 - 7.5, y + 4.5, x1, y, color))


def build_segmentation(theme):
    p = PALETTES[theme]
    o = []
    W, H = 960, 702
    o.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" '
             'height="%d" role="img" aria-labelledby="t d">' % (W, H, W, H))
    o.append("<title id=\"t\">Segmentation du banc d'essai</title>")
    o.append('<desc id="d">Internet et l\'accès distant Zero Trust convergent vers un pare-feu '
             'OPNsense avec Suricata en coupure, qui dessert six VLAN isolés : DMZ, services, '
             'sécurité, management, formation et laboratoire cloisonné. Les sauvegardes sont '
             'chiffrées, sorties hors site et rejouées dans un bac à sable réseau isolé.</desc>')
    o.append('<rect x="0" y="0" width="%d" height="%d" rx="14" fill="%s"/>' % (W, H, p["bg"]))
    o.append('<rect x="0.6" y="0.6" width="%s" height="%s" rx="14" fill="none" stroke="%s" '
             'stroke-width="1.2"/>' % (W - 1.2, H - 1.2, p["line"]))

    o.append(text(28, 33, "BANC D'ESSAI", 12.5, "accent", "700", MONO, ls="2.4", p=p))
    o.append(text(932, 33, "six segments  ·  un seul point de passage  ·  rien ne traverse par défaut",
                  11, "muted", "400", SANS, anchor="end", p=p))
    o.append('<path d="M24 50 L936 50" stroke="%s" stroke-width="1"/>' % p["line"])

    for x, t1, t2 in ((196, "Internet (WAN)", "aucun port entrant ouvert"),
                      (512, "Cloudflare Zero Trust", "tunnel sortant, accès nominatif")):
        o.append('<rect x="%s" y="68" width="252" height="44" rx="8" fill="%s" stroke="%s" '
                 'stroke-width="1"/>' % (x, p["panel"], p["line"]))
        o.append(text(x + 16, 87, t1, 12.5, "text", "600", SANS, p=p))
        o.append(text(x + 16, 103, t2, 10.2, "muted", "400", SANS, p=p))
        o.append(arrow_down(x + 126, 112, 136, p["muted"]))

    o.append('<rect x="24" y="136" width="912" height="58" rx="9" fill="%s" stroke="%s" '
             'stroke-width="1.6"/>' % (p["panel2"], p["accent"]))
    o.append(text(46, 163, "OPNsense — blocage par défaut", 14.5, "text", "700", SANS, p=p))
    o.append(text(46, 182, "Suricata IDS/IPS en coupure  ·  Unbound en DNS split-horizon  ·  "
                           "toute ouverture est écrite et journalisée", 10.8, "muted", "400", SANS, p=p))
    o.append('<rect x="744" y="151" width="172" height="26" rx="13" fill="none" stroke="%s" '
             'stroke-width="1"/>' % p["accent"])
    o.append(text(830, 168, "point de passage unique", 10.2, "accent", "600", SANS,
                  anchor="middle", p=p))

    o.append('<path d="M480 194 L480 212 L56 212 L56 558" stroke="%s" stroke-width="1.6" '
             'fill="none" stroke-linejoin="round"/>' % p["line"])

    for i, (vlan, cidr, name, desc, tag, tone) in enumerate(ROWS):
        top = 232 + i * 60
        cy = top + 26
        col = p[tone]
        o.append('<circle cx="56" cy="%s" r="2.8" fill="%s"/>' % (cy, col))
        o.append('<path d="M56 %s L88 %s" stroke="%s" stroke-width="1.4"/>' % (cy, cy, p["line"]))
        o.append('<rect x="88" y="%s" width="848" height="52" rx="8" fill="%s" stroke="%s" '
                 'stroke-width="1"/>' % (top, p["panel"], p["line"]))
        o.append('<path d="M91.5 %s L91.5 %s" stroke="%s" stroke-width="3.5" '
                 'stroke-linecap="round"/>' % (top + 6, top + 46, col))
        o.append(text(108, top + 21 if cidr else top + 31, vlan, 12.5, tone, "700", MONO, p=p))
        if cidr:
            o.append(text(108, top + 38, cidr, 10.2, "muted", "400", MONO, p=p))
        o.append(text(232, top + 21, name, 13, "text", "600", SANS, p=p))
        o.append(text(232, top + 38, desc, 11.2, "muted", "400", SANS, p=p))
        o.append(text(920, top + 31, tag, 10.6, "muted", "500", SANS, anchor="end", ls="0.4", p=p))

    o.append('<path d="M56 558 L56 623" stroke="%s" stroke-width="1.4" stroke-dasharray="3 4" '
             'fill="none"/>' % p["line"])
    o.append(arrow_right(56, 88, 623, p["line"], dash="3 4"))
    o.append('<rect x="88" y="597" width="848" height="52" rx="8" fill="none" stroke="%s" '
             'stroke-width="1" stroke-dasharray="4 4"/>' % p["line"])
    o.append(text(108, 618, "Sauvegardes — chiffrées, copiées hors site", 12.5, "text", "600", SANS, p=p))
    o.append(text(108, 636, "et rejouées : la restauration est testée dans un bac à sable réseau "
                            "isolé, temps de reprise mesuré", 11.2, "muted", "400", SANS, p=p))
    o.append(text(28, 678, "Aucun flux inter-VLAN par défaut. Chaque ouverture est nommée, "
                           "justifiée, et se retrouve dans les journaux.", 10.8, "muted", "400", SANS, p=p))

    o.append('<g transform="translate(902 660)" opacity="0.85">'
             '<path d="M11 0 C4.9 0 0 4.9 0 11 L0 24 L3.7 20.6 L7.3 24 L11 20.6 L14.7 24 '
             'L18.3 20.6 L22 24 L22 11 C22 4.9 17.1 0 11 0 Z" fill="%s"/>'
             '<circle cx="7.2" cy="10.4" r="1.9" fill="%s"/>'
             '<circle cx="14.8" cy="10.4" r="1.9" fill="%s"/></g>'
             % (p["accent"], p["bg"], p["bg"]))

    o.append('</svg>')
    return "\n".join(o) + "\n"


# ===========================================================================
#  3. Specter — une seule variante : le vert de marque tient sur les deux fonds
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
        for name, fn in (("terminal", build_terminal), ("segmentation", build_segmentation)):
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
