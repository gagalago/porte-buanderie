#!/usr/bin/env python3
"""
Dessins techniques cotes des pieces de charniere (4-bar linkage).

Genere des SVG pour:
1. Platine murale monobloc (A+B en une piece, pliage en Z)
2. Platine porte monobloc (a+b, semelle + 2 pattes)
3. Bras (2 types: 675mm et 446mm)
4. Axe de pivot
5. Vue d'assemblage
"""
import numpy as np
import svgwrite
import math
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'calculs'))
from optimisation_documentee import OW, DT, DW, RWD, SBR

# Parametres solution
Ax, Ay = 1246.1, 471.3
Bx, By = 1188.4, 586.1
ax_d, ay_d = 664.1, 426.3
bx_d, by_d = 766.2, 540.6

# Dimensions derivees
L1 = math.sqrt((Ax-ax_d)**2 + (Ay-ay_d)**2)  # 675mm
L2 = math.sqrt((Bx-bx_d)**2 + (By-by_d)**2)  # 446mm
PATTE_A = ay_d - DT   # 95mm
PATTE_B = by_d - DT   # 189mm
ENTRAXE_MUR_X = abs(Ax - Bx)  # 50mm
ENTRAXE_MUR_Y = abs(Ay - By)  # 104mm
ENTRAXE_PORTE_X = abs(ax_d - bx_d)  # 180mm
ENTRAXE_PORTE_Y = abs(ay_d - by_d)  # 94mm
OFFSET_B = By - RWD  # 107mm (B est 107mm dans la buanderie)
OFFSET_A = Ay - RWD  # 3mm (A est quasi a fleur)

# Dimensions des pieces
TOLE = 6         # epaisseur tole platines (mm)
TUBE_PAL_EXT = 22  # tube palier exterieur
TUBE_PAL_INT = 16  # tube palier interieur (axe)
TUBE_PAL_H = 50    # hauteur tube palier
AXE_D = 16       # diametre axe
AXE_L = 80       # longueur axe
BRAS_TUBE = (50, 30, 3)  # tube rect: largeur, hauteur, epaisseur
PLAT_EXT = (80, 50, 10)  # plat d'extremite bras: largeur, hauteur, ep.
BAGUE = (16, 22, 20)     # bague: D.int, D.ext, longueur
PATTE_A_TUBE = (40, 40, 3)  # tube carre patte a
PATTE_B_TUBE = (50, 50, 4)  # tube carre patte b
SEMELLE_W = 80   # largeur semelle
SEMELLE_EP = 8   # epaisseur semelle

outdir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'exports')
os.makedirs(outdir, exist_ok=True)

# =============================================================================
# Utilitaires SVG
# =============================================================================
def new_dwg(name, width, height):
    return svgwrite.Drawing(os.path.join(outdir, name),
                            size=(f'{width}px', f'{height}px'))

def line(dwg, x1, y1, x2, y2, **kw):
    kw.setdefault('stroke', 'black')
    kw.setdefault('stroke_width', 1)
    dwg.add(dwg.line(start=(x1,y1), end=(x2,y2), **kw))

def rect(dwg, x, y, w, h, **kw):
    kw.setdefault('stroke', 'black')
    kw.setdefault('stroke_width', 1)
    kw.setdefault('fill', 'none')
    dwg.add(dwg.rect(insert=(x,y), size=(w,h), **kw))

def circle(dwg, cx, cy, r, **kw):
    kw.setdefault('stroke', 'black')
    kw.setdefault('stroke_width', 1)
    kw.setdefault('fill', 'none')
    dwg.add(dwg.circle(center=(cx,cy), r=r, **kw))

def text(dwg, x, y, txt, **kw):
    kw.setdefault('font_size', '10px')
    kw.setdefault('font_family', 'Arial')
    kw.setdefault('text_anchor', 'middle')
    dwg.add(dwg.text(txt, insert=(x,y), **kw))

def dim_h(dwg, x1, x2, y, label, gap=15):
    """Cote horizontale avec fleches."""
    line(dwg, x1, y, x2, y, stroke='#333', stroke_width=0.5)
    line(dwg, x1, y-gap, x1, y+5, stroke='#333', stroke_width=0.3)
    line(dwg, x2, y-gap, x2, y+5, stroke='#333', stroke_width=0.3)
    # Fleches
    for xx, d in [(x1, 3), (x2, -3)]:
        line(dwg, xx, y, xx+d, y-2, stroke='#333', stroke_width=0.5)
        line(dwg, xx, y, xx+d, y+2, stroke='#333', stroke_width=0.5)
    text(dwg, (x1+x2)/2, y-3, label, font_size='9px', fill='#333')

def dim_v(dwg, x, y1, y2, label, gap=15):
    """Cote verticale avec fleches."""
    line(dwg, x, y1, x, y2, stroke='#333', stroke_width=0.5)
    line(dwg, x-5, y1, x+gap, y1, stroke='#333', stroke_width=0.3)
    line(dwg, x-5, y2, x+gap, y2, stroke='#333', stroke_width=0.3)
    for yy, d in [(y1, 3), (y2, -3)]:
        line(dwg, x, yy, x-2, yy+d, stroke='#333', stroke_width=0.5)
        line(dwg, x, yy, x+2, yy+d, stroke='#333', stroke_width=0.5)
    mid = (y1+y2)/2
    dwg.add(dwg.text(label, insert=(x+gap+2, mid+3), font_size='9px',
                      font_family='Arial', fill='#333'))

def title(dwg, x, y, txt):
    text(dwg, x, y, txt, font_size='14px', font_weight='bold')

def subtitle(dwg, x, y, txt):
    text(dwg, x, y, txt, font_size='10px', fill='gray')

# =============================================================================
# 1. PLATINE MURALE MONOBLOC (vue de profil + vue de face)
# =============================================================================
def plan_platine_murale():
    S = 1.0
    W, H = 1200, 1000
    dwg = new_dwg('platine_murale.svg', W, H)

    title(dwg, W/2, 25, 'PLATINE MURALE MONOBLOC (x2: haut + bas)')
    subtitle(dwg, W/2, 42, f'Tole acier 6mm, 2 pliages a 90 deg, goussets soudes d\'un cote')

    # Dimensions de la piece
    PLAT_BASE_W = 200    # largeur plaque base (le long du mur)
    PLAT_BASE_D = 60     # profondeur plaque base (depuis face mur)
    MONTANT_H = OFFSET_B # 107mm (hauteur du Z)
    PLAT_TOP_W = 150     # largeur plaque top
    PLAT_TOP_D = 60      # profondeur plaque top
    GOUSSET = 80         # taille goussets

    # =================================================================
    # VUE 1: TOLE DEPLIEE (patron de decoupe) — en haut
    # Avec languette gousset integree (1 seule soudure au bout)
    # =================================================================
    text(dwg, 400, 80, '1. TOLE DEPLIEE (patron avant pliage)', font_size='12px', font_weight='bold')
    text(dwg, 400, 95, 'Decouper cette forme dans une tole de 6mm — gousset integre', font_size='9px', fill='gray')

    ox1, oy1 = 80, 130
    S1 = 1.0  # echelle

    # Le patron est un contour unique:
    # - Plat base (200 x 60mm) avec languette gousset a droite
    # - Montant (200 x 107mm) — meme largeur que base, mais la languette depasse
    # - Plat top (150 x 60mm) — plus etroit
    #
    # La languette part du bord droit du plat base et longe le montant.
    # Apres pliage, elle se retrouve plaquee contre le montant = gousset.

    LANG_W = GOUSSET  # 80mm de large (deviendra la hauteur du gousset sur le montant)

    # Contour du patron (polygone unique)
    pts_patron = [
        # Plat base (coin bas-gauche, sens horaire)
        (ox1, oy1),                                              # 0: bas-gauche base
        (ox1 + PLAT_BASE_W*S1, oy1),                            # 1: bas-droite base
        (ox1 + PLAT_BASE_W*S1, oy1 + PLAT_BASE_D*S1),          # 2: ligne pliage 1, droite
        # Languette gousset (part du bord droit, le long du montant)
        (ox1 + PLAT_BASE_W*S1 + LANG_W*S1, oy1 + PLAT_BASE_D*S1),  # 3: debut languette
        (ox1 + PLAT_BASE_W*S1 + LANG_W*S1, oy1 + (PLAT_BASE_D + MONTANT_H)*S1),  # 4: fin languette (bout)
        (ox1 + PLAT_BASE_W*S1, oy1 + (PLAT_BASE_D + MONTANT_H)*S1),  # 5: retour au montant
        # Ligne pliage 2
        (ox1 + PLAT_TOP_W*S1, oy1 + (PLAT_BASE_D + MONTANT_H)*S1),  # 6: debut plat top droite
        (ox1 + PLAT_TOP_W*S1, oy1 + (PLAT_BASE_D + MONTANT_H + PLAT_TOP_D)*S1),  # 7: bas-droite top
        (ox1, oy1 + (PLAT_BASE_D + MONTANT_H + PLAT_TOP_D)*S1),  # 8: bas-gauche top
        (ox1, oy1),                                              # 9: retour depart
    ]

    # Dessiner le contour
    dwg.add(dwg.polygon(points=pts_patron, fill='#d8d8d8', stroke='black', stroke_width=2))

    # Zones colorees pour distinguer les parties
    # Plat base
    rect(dwg, ox1+1, oy1+1, PLAT_BASE_W*S1-2, PLAT_BASE_D*S1-2,
         fill='#d0d0d0', stroke='none')
    text(dwg, ox1 + PLAT_BASE_W*S1/2, oy1 + PLAT_BASE_D*S1/2 + 3,
         f'PLAT BASE\n{PLAT_BASE_W}x{PLAT_BASE_D}mm', font_size='8px')

    # Montant (zone qui sera pliee)
    rect(dwg, ox1+1, oy1 + PLAT_BASE_D*S1+1, PLAT_BASE_W*S1-2, MONTANT_H*S1-2,
         fill='#e8e8e8', stroke='none')
    text(dwg, ox1 + PLAT_BASE_W*S1/2, oy1 + PLAT_BASE_D*S1 + MONTANT_H*S1/2 + 3,
         f'MONTANT\n(pliage)\n{MONTANT_H}mm', font_size='8px', fill='#888')

    # Languette gousset
    rect(dwg, ox1 + PLAT_BASE_W*S1+1, oy1 + PLAT_BASE_D*S1+1,
         LANG_W*S1-2, MONTANT_H*S1-2,
         fill='#ffe0b0', stroke='none')
    text(dwg, ox1 + PLAT_BASE_W*S1 + LANG_W*S1/2,
         oy1 + PLAT_BASE_D*S1 + MONTANT_H*S1/2 + 3,
         f'LANGUETTE\nGOUSSET\n{LANG_W}x{MONTANT_H}mm\n(se plie contre\nle montant)',
         font_size='7px', fill='#b07000')

    # Plat top
    mont_bottom = oy1 + (PLAT_BASE_D + MONTANT_H)*S1
    rect(dwg, ox1+1, mont_bottom+1, PLAT_TOP_W*S1-2, PLAT_TOP_D*S1-2,
         fill='#d0d0d0', stroke='none')
    text(dwg, ox1 + PLAT_TOP_W*S1/2, mont_bottom + PLAT_TOP_D*S1/2 + 3,
         f'PLAT TOP\n{PLAT_TOP_W}x{PLAT_TOP_D}mm', font_size='8px')

    # Trou pivot A (dans le plat base)
    circle(dwg, ox1 + 40*S1, oy1 + PLAT_BASE_D*S1/2, AXE_D/2*S1,
           fill='white', stroke='red', stroke_width=2)
    text(dwg, ox1 + 40*S1, oy1 - 8, 'A', font_size='9px', fill='red', font_weight='bold')

    # Trous chevilles M12
    for dx in [80, 130, 180]:
        circle(dwg, ox1 + dx*S1, oy1 + PLAT_BASE_D*S1/2, 5, fill='#555', stroke='black')

    # Trou pivot B (dans le plat top)
    circle(dwg, ox1 + 50*S1, mont_bottom + PLAT_TOP_D*S1/2, AXE_D/2*S1,
           fill='white', stroke='blue', stroke_width=2)
    text(dwg, ox1 + 50*S1, mont_bottom + PLAT_TOP_D*S1 + 15, 'B',
         font_size='9px', fill='blue', font_weight='bold')

    # Lignes de pliage (tirets rouges)
    pliage1_y = oy1 + PLAT_BASE_D*S1
    line(dwg, ox1, pliage1_y, ox1 + PLAT_BASE_W*S1, pliage1_y,
         stroke='#e00', stroke_width=1.5, stroke_dasharray='8,4')
    text(dwg, ox1 - 5, pliage1_y + 3, 'pliage 1 ->', font_size='8px', fill='#e00', text_anchor='end')

    pliage2_y = mont_bottom
    line(dwg, ox1, pliage2_y, ox1 + PLAT_TOP_W*S1, pliage2_y,
         stroke='#e00', stroke_width=1.5, stroke_dasharray='8,4')
    text(dwg, ox1 - 5, pliage2_y + 3, 'pliage 2 ->', font_size='8px', fill='#e00', text_anchor='end')

    # Pliage de la languette (elle se plie contre le montant)
    line(dwg, ox1 + PLAT_BASE_W*S1, pliage1_y, ox1 + PLAT_BASE_W*S1, pliage2_y,
         stroke='#e00', stroke_width=1.5, stroke_dasharray='8,4')
    text(dwg, ox1 + PLAT_BASE_W*S1 + LANG_W*S1 + 10,
         pliage1_y + MONTANT_H*S1/2, 'pliage 3\n(languette\nse rabat\ncontre\nle montant)',
         font_size='7px', fill='#e00', text_anchor='start')

    # Note soudure
    text(dwg, ox1 + PLAT_BASE_W*S1 + LANG_W*S1/2,
         pliage2_y + 15, '1 soudure ici\n(bout de languette\nsur plat top)',
         font_size='7px', fill='#c00')

    # Cotes
    dim_h(dwg, ox1, ox1 + PLAT_BASE_W*S1, oy1 - 15, f'{PLAT_BASE_W}mm', gap=8)
    dim_h(dwg, ox1 + PLAT_BASE_W*S1, ox1 + (PLAT_BASE_W + LANG_W)*S1,
          oy1 - 15, f'{LANG_W}mm', gap=8)
    total_w = PLAT_BASE_W + LANG_W
    dim_h(dwg, ox1, ox1 + total_w*S1, oy1 - 35, f'{total_w}mm (total)', gap=8)
    dim_v(dwg, ox1 + total_w*S1 + 40, oy1, oy1 + PLAT_BASE_D*S1,
          f'{PLAT_BASE_D}mm', gap=10)
    dim_v(dwg, ox1 + total_w*S1 + 40, pliage1_y, pliage2_y,
          f'{MONTANT_H}mm', gap=10)
    dim_v(dwg, ox1 + total_w*S1 + 40, pliage2_y,
          pliage2_y + PLAT_TOP_D*S1, f'{PLAT_TOP_D}mm', gap=10)

    # =================================================================
    # VUE 2: PROFIL PLIE (vue de cote) — milieu gauche
    # =================================================================
    text(dwg, 250, 400, '2. VUE DE PROFIL (piece pliee, vue de cote)', font_size='12px', font_weight='bold')

    ox2, oy2 = 200, 930  # bas du mur — assez bas pour que le haut ne chevauche pas le titre
    S2 = 0.7  # echelle reduite

    # Mur (fond gris)
    rect(dwg, ox2 - 70, oy2 - RWD*S2, 70, RWD*S2, fill='#e8e8e8', stroke='#bbb')
    text(dwg, ox2 - 35, oy2 - RWD*S2/2, 'MUR', font_size='9px', fill='#999')

    # Plaque base — horizontale, plaquee sur la face buanderie du mur
    base_x2 = ox2
    base_y2 = oy2 - RWD*S2  # face buanderie
    rect(dwg, base_x2, base_y2 - TOLE*S2, PLAT_BASE_D*S2, TOLE*S2,
         fill='#b0b0b0', stroke='black', stroke_width=2)
    circle(dwg, base_x2 + 30*S2, base_y2 - TOLE*S2/2, AXE_D/2*S2,
           fill='white', stroke='red', stroke_width=2)
    text(dwg, base_x2 + 30*S2, base_y2 - TOLE*S2 - 12, 'A', font_size='10px', fill='red', font_weight='bold')

    # Montant — vertical, part du bout du plat base vers la buanderie
    mont_x2 = base_x2 + PLAT_BASE_D*S2 - TOLE*S2
    mont_y2_top = base_y2 - MONTANT_H*S2
    rect(dwg, mont_x2, mont_y2_top, TOLE*S2, MONTANT_H*S2,
         fill='#b0b0b0', stroke='black', stroke_width=2)

    # Plaque top — horizontale, en porte-a-faux dans la buanderie
    top_x2 = mont_x2 - PLAT_TOP_D*S2 + TOLE*S2
    top_y2 = mont_y2_top - TOLE*S2
    rect(dwg, top_x2, top_y2, PLAT_TOP_D*S2, TOLE*S2,
         fill='#b0b0b0', stroke='black', stroke_width=2)
    circle(dwg, top_x2 + PLAT_TOP_D*S2/2, top_y2 + TOLE*S2/2, AXE_D/2*S2,
           fill='white', stroke='blue', stroke_width=2)
    text(dwg, top_x2 + PLAT_TOP_D*S2/2, top_y2 - 12, 'B', font_size='10px', fill='blue', font_weight='bold')

    # Languette gousset (rabattue contre le montant, 1 seul cote)
    lang_w2 = LANG_W * S2  # 80mm = epaisseur de la languette vu de profil -> c'est la tole ep.6mm
    # Vue de profil: la languette est plaquee contre le montant, on voit son epaisseur (6mm)
    rect(dwg, mont_x2 + TOLE*S2, mont_y2_top, TOLE*S2, MONTANT_H*S2,
         fill='#ffe0b0', stroke='black', stroke_width=1)
    text(dwg, mont_x2 + TOLE*S2*2 + 5, mont_y2_top + MONTANT_H*S2/2,
         'languette\ngousset\n(rabattue)', font_size='7px', fill='#b07000', text_anchor='start')
    # Annotation soudure au bout
    text(dwg, mont_x2 + TOLE*S2*2 + 5, mont_y2_top - 5,
         '* soudure', font_size='6px', fill='#c00', text_anchor='start')

    # Annotations pliages
    text(dwg, base_x2 + PLAT_BASE_D*S2 + 15, base_y2 - TOLE*S2/2, 'pliage 1',
         font_size='7px', fill='#e00', text_anchor='start')
    text(dwg, mont_x2 + TOLE*S2/2, mont_y2_top - 15, 'pliage 2',
         font_size='7px', fill='#e00')

    # Cotes profil
    dim_v(dwg, mont_x2 + TOLE*S2*3 + 20, base_y2 - TOLE*S2, top_y2 + TOLE*S2,
          f'{MONTANT_H}mm', gap=10)
    dim_h(dwg, base_x2, base_x2 + PLAT_BASE_D*S2, oy2 + 15, f'{PLAT_BASE_D}mm', gap=10)

    # Labels
    text(dwg, ox2 - 35, oy2 + 12, 'cuisine', font_size='7px', fill='#c65100')
    text(dwg, top_x2, top_y2 - 30, 'buanderie', font_size='8px', fill='#1565c0')

    # Chevilles M12
    for d in [15, 35]:
        cx = base_x2 + d*S2
        circle(dwg, cx, base_y2 - TOLE*S2/2, 3, fill='#555', stroke='black')
    text(dwg, base_x2 + 25*S2, oy2 + 30, 'chevilles M12', font_size='7px', fill='#555')

    # Fleche montrant le cote libre pour bras
    line(dwg, mont_x2 - 50, base_y2 - MONTANT_H*S2/2, mont_x2 - 5, base_y2 - MONTANT_H*S2/2,
         stroke='#aaa', stroke_width=0.5, stroke_dasharray='3,3')
    text(dwg, mont_x2 - 55, base_y2 - MONTANT_H*S2/2, 'bras\n(libre)', font_size='7px', fill='#aaa', text_anchor='end')

    # =================================================================
    # VUE 3: VUE DE DESSUS (piece pliee) — milieu droite
    # =================================================================
    text(dwg, 850, 400, '3. VUE DE DESSUS (piece pliee)', font_size='12px', font_weight='bold')

    ox3, oy3 = 700, 700
    S3 = 1.0

    # Plaque base (rectangle horizontal sur le mur)
    rect(dwg, ox3, oy3, PLAT_BASE_W*S3, PLAT_BASE_D*S3,
         fill='#d0d0d0', stroke='black', stroke_width=1.5)
    text(dwg, ox3 + PLAT_BASE_W*S3/2, oy3 + PLAT_BASE_D*S3 + 15,
         'plaque base (sur mur)', font_size='8px', fill='#888')
    # Pivot A
    circle(dwg, ox3 + 40*S3, oy3 + PLAT_BASE_D*S3/2, AXE_D/2*S3,
           fill='white', stroke='red', stroke_width=2)
    text(dwg, ox3 + 40*S3, oy3 - 8, 'A', font_size='9px', fill='red', font_weight='bold')
    # Chevilles
    for dx in [80, 130, 180]:
        circle(dwg, ox3 + dx*S3, oy3 + PLAT_BASE_D*S3/2, 4, fill='#555', stroke='black')

    # Montant (bande etroite vers le haut = vers buanderie)
    rect(dwg, ox3, oy3 - MONTANT_H*S3, TOLE*S3, MONTANT_H*S3,
         fill='#b0b0b0', stroke='black', stroke_width=1)

    # Plaque top (en porte-a-faux, dans la buanderie)
    rect(dwg, ox3 - 20*S3, oy3 - MONTANT_H*S3 - PLAT_TOP_D*S3,
         PLAT_TOP_W*S3, PLAT_TOP_D*S3,
         fill='#d0d0d0', stroke='black', stroke_width=1.5)
    text(dwg, ox3 + PLAT_TOP_W*S3/2 - 20*S3,
         oy3 - MONTANT_H*S3 - PLAT_TOP_D*S3 - 10,
         'plaque top', font_size='8px', fill='#888')
    # Pivot B
    circle(dwg, ox3 + 50*S3, oy3 - MONTANT_H*S3 - PLAT_TOP_D*S3/2,
           AXE_D/2*S3, fill='white', stroke='blue', stroke_width=2)
    text(dwg, ox3 + 50*S3 + 20, oy3 - MONTANT_H*S3 - PLAT_TOP_D*S3/2 + 3,
         'B', font_size='9px', fill='blue', font_weight='bold')

    # Gousset (triangle d'un cote)
    g3 = GOUSSET * S3
    dwg.add(dwg.polygon(
        points=[(ox3 + TOLE*S3, oy3),
                (ox3 + TOLE*S3 + g3, oy3),
                (ox3 + TOLE*S3, oy3 - g3)],
        fill='#e0e0e0', stroke='black', stroke_width=0.5))
    text(dwg, ox3 + TOLE*S3 + g3/3, oy3 - g3/3, 'gousset', font_size='7px', fill='#555')

    # Cotes
    dim_v(dwg, ox3 + PLAT_BASE_W*S3 + 15, oy3, oy3 - MONTANT_H*S3,
          f'{MONTANT_H}mm', gap=10)
    dim_h(dwg, ox3, ox3 + PLAT_BASE_W*S3, oy3 + PLAT_BASE_D*S3 + 30,
          f'{PLAT_BASE_W}mm', gap=10)

    # Labels direction
    text(dwg, ox3 - 30, oy3 + PLAT_BASE_D*S3/2, 'MUR ->', font_size='8px', fill='#999', text_anchor='end')
    text(dwg, ox3 - 30, oy3 - MONTANT_H*S3, 'BUANDERIE', font_size='8px', fill='#1565c0', text_anchor='end')

    # =================================================================
    # Materiel
    # =================================================================
    text(dwg, W/2, H - 30, f'Tole S235 ep.{TOLE}mm | 2 pliages 90 deg | Goussets tole 5mm soudes d\'un cote (oppose aux bras)',
         font_size='9px', fill='#555')
    text(dwg, W/2, H - 15, f'Pivots = boulons D{AXE_D}mm traversant la tole | Fixation mur: 3x chevilles chimiques M12',
         font_size='9px', fill='#555')

    dwg.save()
    print(f"  {dwg.filename}")


# =============================================================================
# 2. PLATINE PORTE MONOBLOC (vue de dessus + vue de profil)
# =============================================================================
def plan_platine_porte():
    S = 1.2
    W, H = 1200, 1400
    dwg = new_dwg('platine_porte.svg', W, H)

    title(dwg, W/2, 25, 'PLATINE PORTE MONOBLOC (x2: haut + bas)')
    subtitle(dwg, W/2, 42, f'Semelle + 2 pattes (a: {PATTE_A:.0f}mm, b: {PATTE_B:.0f}mm)')

    # --- Vue de face (depuis buanderie, pattes vers le haut) ---
    text(dwg, 350, 70, 'VUE DE FACE (depuis buanderie)', font_size='11px', font_weight='bold')

    ox, oy = 120, 500  # bien espace en haut
    # La porte est en bas (face arriere en haut)

    # Face arriere porte (ligne)
    porte_w = 400 * S
    line(dwg, ox, oy, ox + porte_w, oy, stroke='green', stroke_width=2, stroke_dasharray='8,4')
    text(dwg, ox + porte_w/2, oy + 15, 'face arriere porte (y=355)', font_size='8px', fill='green')

    # Semelle
    sem_x1 = ox + (ax_d - 563 + 563 - ENTRAXE_PORTE_X/2 - 40) * S  # centree entre a et b
    # Simplifions: la semelle va de 50mm avant patte_a a 50mm apres patte_b
    pa_screen_x = ox + 100 * S  # position patte a sur l'ecran
    pb_screen_x = ox + (100 + ENTRAXE_PORTE_X) * S
    sem_margin = 40 * S
    sem_x = pa_screen_x - sem_margin
    sem_w = (ENTRAXE_PORTE_X + 80) * S
    sem_h = SEMELLE_W * S
    rect(dwg, sem_x, oy - sem_h, sem_w, sem_h, fill='#e0d0c0', stroke='black', stroke_width=1.5)
    text(dwg, sem_x + sem_w/2, oy - sem_h/2 + 3, f'Semelle {ENTRAXE_PORTE_X+80:.0f}x{SEMELLE_W}x{SEMELLE_EP}mm',
         font_size='8px')

    # Boulons M8 sur semelle (6 par patte = 12 total)
    for px_base, n in [(pa_screen_x, 'a'), (pb_screen_x, 'b')]:
        for dx in [-15, 0, 15]:
            for dy in [-20, 20]:
                circle(dwg, px_base + dx*S, oy - sem_h/2 + dy*S, 3, fill='#555')

    # Patte a (tube carre, vers le haut = vers buanderie)
    pa_w = PATTE_A_TUBE[0] * S
    pa_h = PATTE_A * S
    pa_top = oy - sem_h - pa_h
    rect(dwg, pa_screen_x - pa_w/2, pa_top, pa_w, pa_h,
         fill='#ffcccc', stroke='red', stroke_width=1.5)
    # Pivot a — boulon qui traverse la patte (trou dans le tube)
    pivot_a_y = pa_top + 20*S  # 20mm du bout, dans le corps de la patte
    circle(dwg, pa_screen_x, pivot_a_y, AXE_D/2*S,
           fill='white', stroke='red', stroke_width=2)
    text(dwg, pa_screen_x, pa_top - 8, 'Pivot a', font_size='9px', fill='red', font_weight='bold')
    text(dwg, pa_screen_x + pa_w/2 + 5, pivot_a_y + 3, f'boulon D{AXE_D}\ndans la patte', font_size='7px', fill='red', text_anchor='start')

    # Patte b (tube carre, plus long)
    pb_w = PATTE_B_TUBE[0] * S
    pb_h = PATTE_B * S
    pb_top = oy - sem_h - pb_h
    rect(dwg, pb_screen_x - pb_w/2, pb_top, pb_w, pb_h,
         fill='#ccccff', stroke='blue', stroke_width=1.5)
    # Pivot b — boulon qui traverse la patte
    pivot_b_y = pb_top + 20*S
    circle(dwg, pb_screen_x, pivot_b_y, AXE_D/2*S,
           fill='white', stroke='blue', stroke_width=2)
    text(dwg, pb_screen_x, pb_top - 8, 'Pivot b', font_size='9px', fill='blue', font_weight='bold')
    text(dwg, pb_screen_x + pb_w/2 + 5, pivot_b_y + 3, f'boulon D{AXE_D}\ndans la patte', font_size='7px', fill='blue', text_anchor='start')

    # Goussets JUSQU'AU BOUT des pattes — UN SEUL COTE (oppose au bras)
    # Triangle de la semelle jusqu'a l'extremite de la patte
    for px, patte_h, tube_w, color in [
        (pa_screen_x, pa_h, PATTE_A_TUBE[0], '#ffdddd'),
        (pb_screen_x, pb_h, PATTE_B_TUBE[0], '#ddddff'),
    ]:
        side = -1  # gousset a gauche (oppose au bras qui arrive par la droite)
        pw = tube_w/2*S
        g_base = 60 * S  # largeur a la base (sur la semelle)
        dwg.add(dwg.polygon(
            points=[(px + side*pw, oy - sem_h),           # base de la patte (jonction semelle)
                    (px + side*pw, oy - sem_h - patte_h),  # bout de la patte
                    (px + side*(pw + g_base), oy - sem_h)], # base elargie sur la semelle
            fill=color, stroke='black', stroke_width=0.8))

    text(dwg, pa_screen_x - PATTE_A_TUBE[0]/2*S - 35, oy - sem_h - pa_h/2,
         'gousset\njusqu\'au bout\n(1 cote)', font_size='7px', fill='#555')

    # Annotation: cote libre pour le bras
    text(dwg, pb_screen_x + PATTE_B_TUBE[0]/2*S + 10, oy - sem_h - pb_h/2,
         'cote bras\n(libre)', font_size='7px', fill='#aaa', text_anchor='start')

    # Cotes
    dim_h(dwg, pa_screen_x, pb_screen_x, oy + 30, f'entraxe {ENTRAXE_PORTE_X:.0f}mm', gap=10)
    dim_v(dwg, pb_screen_x + 60, oy - sem_h, oy - sem_h - pb_h,
          f'patte b: {PATTE_B:.0f}mm', gap=10)
    dim_v(dwg, pa_screen_x - 50, oy - sem_h, oy - sem_h - pa_h,
          f'patte a: {PATTE_A:.0f}mm', gap=-10)

    # --- Vue de profil (coupe) --- au milieu a droite
    text(dwg, 850, 70, 'VUE DE PROFIL (coupe)', font_size='11px', font_weight='bold')

    ox3, oy3 = 750, 450
    # Porte (rectangle)
    porte_h = DT * S * 0.5  # echelle reduite pour le profil
    porte_w_p = 120 * S
    rect(dwg, ox3, oy3 - porte_h, porte_w_p, porte_h, fill='#c8e6c9', stroke='green', stroke_width=1.5)
    text(dwg, ox3 + porte_w_p/2, oy3 - porte_h/2 + 3, 'PORTE', font_size='9px', fill='green')
    text(dwg, ox3 + porte_w_p/2, oy3 + 12, 'face cuisine', font_size='7px', fill='#888')
    text(dwg, ox3 + porte_w_p/2, oy3 - porte_h - 8, 'face buanderie', font_size='7px', fill='#888')

    # Semelle (sur face arriere)
    sem_p_w = 80 * S * 0.5
    sem_p_h = SEMELLE_EP * S
    sem_p_x = ox3 + porte_w_p/2 - sem_p_w/2
    sem_p_y = oy3 - porte_h - sem_p_h
    rect(dwg, sem_p_x, sem_p_y, sem_p_w, sem_p_h, fill='#e0d0c0', stroke='black', stroke_width=1)
    text(dwg, sem_p_x + sem_p_w + 5, sem_p_y + sem_p_h/2 + 3,
         f'semelle {SEMELLE_EP}mm', font_size='7px', fill='#555', text_anchor='start')

    # Contre-plaque interieure
    cp_y = oy3 - porte_h + 5
    rect(dwg, sem_p_x + 5, cp_y, sem_p_w - 10, 3*S, fill='#999', stroke='black', stroke_width=0.5)
    text(dwg, sem_p_x + sem_p_w + 5, cp_y + 5,
         'contre-plaque 3mm', font_size='7px', fill='#555', text_anchor='start')

    # Patte (tube carre, part de la semelle)
    patte_p_w = 30 * S * 0.5
    patte_p_h = 120 * S * 0.5  # represente la patte
    patte_p_x = ox3 + porte_w_p/2 - patte_p_w/2
    patte_p_y = sem_p_y - patte_p_h
    rect(dwg, patte_p_x, patte_p_y, patte_p_w, patte_p_h, fill='#ffcccc', stroke='red', stroke_width=1)

    # Gousset profil
    dwg.add(dwg.polygon(
        points=[(patte_p_x + patte_p_w, sem_p_y),
                (patte_p_x + patte_p_w + 20, sem_p_y),
                (patte_p_x + patte_p_w, patte_p_y + patte_p_h/2)],
        fill='#e0e0e0', stroke='black', stroke_width=0.5))
    text(dwg, patte_p_x + patte_p_w + 22, sem_p_y - 5, 'gousset', font_size='7px', fill='#555', text_anchor='start')

    # Pivot (au bout de la patte)
    circle(dwg, patte_p_x + patte_p_w/2, patte_p_y, 5, fill='white', stroke='red', stroke_width=1.5)

    # Boulons traversants
    for dy in [15, 40, 65]:
        bx = sem_p_x + sem_p_w/2
        by = oy3 - porte_h + dy * S * 0.3
        line(dwg, bx - 20, by, bx + 20, by, stroke='#555', stroke_width=0.5, stroke_dasharray='2,2')
    text(dwg, ox3 + porte_w_p/2, oy3 - porte_h/2 + 25, 'boulons M8\ntraversants',
         font_size='7px', fill='#555')

    # --- Vue de dessus (top-down, X-Y) --- en bas
    text(dwg, W/2, 700, 'VUE DE DESSUS (depuis au-dessus)', font_size='11px', font_weight='bold')

    ox4, oy4 = 150, 1100  # origine en bas
    # Porte = rectangle vert (vu de dessus)
    porte_top_w = (OW - 50) * S * 0.5  # demi-echelle pour la porte
    porte_top_d = DT * S * 0.5
    rect(dwg, ox4, oy4 - porte_top_d, porte_top_w, porte_top_d,
         fill='#c8e6c9', stroke='green', stroke_width=1.5)
    text(dwg, ox4 + porte_top_w/2, oy4 + 12, 'face cuisine (y=0)', font_size='7px', fill='#888')
    text(dwg, ox4 + porte_top_w/2, oy4 - porte_top_d - 8, 'face buanderie (y=355)', font_size='7px', fill='#888')
    text(dwg, ox4 + porte_top_w/2, oy4 - porte_top_d/2 + 3, 'PORTE', font_size='10px', fill='green')

    # Semelle (bande sur la face arriere)
    sem_top_x = ox4 + 150 * S * 0.5  # position relative de la semelle
    sem_top_w = (ENTRAXE_PORTE_X + 80) * S * 0.5
    sem_top_h = SEMELLE_W * S * 0.5
    rect(dwg, sem_top_x, oy4 - porte_top_d - sem_top_h, sem_top_w, sem_top_h,
         fill='#e0d0c0', stroke='black', stroke_width=1)
    text(dwg, sem_top_x + sem_top_w/2, oy4 - porte_top_d - sem_top_h/2 + 3,
         'semelle', font_size='7px', fill='#555')

    # Pattes (rectangles qui partent de la semelle vers la buanderie)
    patte_a_sx = sem_top_x + 40 * S * 0.5
    patte_b_sx = sem_top_x + (40 + ENTRAXE_PORTE_X) * S * 0.5
    pa_top_w = PATTE_A_TUBE[0] * S * 0.5
    pb_top_w = PATTE_B_TUBE[0] * S * 0.5
    pa_top_h = PATTE_A * S * 0.5
    pb_top_h = PATTE_B * S * 0.5

    rect(dwg, patte_a_sx - pa_top_w/2, oy4 - porte_top_d - sem_top_h - pa_top_h,
         pa_top_w, pa_top_h, fill='#ffcccc', stroke='red', stroke_width=1.5)
    rect(dwg, patte_b_sx - pb_top_w/2, oy4 - porte_top_d - sem_top_h - pb_top_h,
         pb_top_w, pb_top_h, fill='#ccccff', stroke='blue', stroke_width=1.5)

    # Pivots (boulons dans les pattes)
    circle(dwg, patte_a_sx, oy4 - porte_top_d - sem_top_h - pa_top_h + 12,
           AXE_D/2*S*0.5, fill='white', stroke='red', stroke_width=1.5)
    circle(dwg, patte_b_sx, oy4 - porte_top_d - sem_top_h - pb_top_h + 12,
           AXE_D/2*S*0.5, fill='white', stroke='blue', stroke_width=1.5)
    text(dwg, patte_a_sx, oy4 - porte_top_d - sem_top_h - pa_top_h - 8,
         'a', font_size='9px', fill='red', font_weight='bold')
    text(dwg, patte_b_sx, oy4 - porte_top_d - sem_top_h - pb_top_h - 8,
         'b', font_size='9px', fill='blue', font_weight='bold')

    # Goussets (triangles d'un seul cote, de la semelle au bout de la patte)
    for px, ph, tw, col in [(patte_a_sx, pa_top_h, pa_top_w, '#ffdddd'),
                             (patte_b_sx, pb_top_h, pb_top_w, '#ddddff')]:
        g_base = 30 * S * 0.5
        dwg.add(dwg.polygon(
            points=[(px - tw/2, oy4 - porte_top_d - sem_top_h),
                    (px - tw/2, oy4 - porte_top_d - sem_top_h - ph),
                    (px - tw/2 - g_base, oy4 - porte_top_d - sem_top_h)],
            fill=col, stroke='black', stroke_width=0.5))

    # Bras (lignes qui partent des pivots vers le mur droit)
    text(dwg, patte_a_sx + 50, oy4 - porte_top_d - sem_top_h - pa_top_h/2,
         f'-> bras 1 ({L1:.0f}mm)', font_size='7px', fill='red', text_anchor='start')
    text(dwg, patte_b_sx + 50, oy4 - porte_top_d - sem_top_h - pb_top_h/2,
         f'-> bras 2 ({L2:.0f}mm)', font_size='7px', fill='blue', text_anchor='start')

    # Cotes
    dim_h(dwg, patte_a_sx, patte_b_sx, oy4 + 25,
          f'entraxe {ENTRAXE_PORTE_X:.0f}mm', gap=10)
    dim_v(dwg, patte_b_sx + 40, oy4 - porte_top_d - sem_top_h,
          oy4 - porte_top_d - sem_top_h - pb_top_h,
          f'{PATTE_B:.0f}mm', gap=10)

    # Materiel
    text(dwg, W/2, H - 30,
         f'Patte a: tube {PATTE_A_TUBE[0]}x{PATTE_A_TUBE[1]}x{PATTE_A_TUBE[2]} L={PATTE_A:.0f}mm | '
         f'Patte b: tube {PATTE_B_TUBE[0]}x{PATTE_B_TUBE[1]}x{PATTE_B_TUBE[2]} L={PATTE_B:.0f}mm',
         font_size='9px', fill='#555')
    text(dwg, W/2, H - 15,
         f'Pivots = boulons D{AXE_D}mm dans les pattes | '
         f'Goussets d\'un seul cote (oppose au bras) jusqu\'au bout | 12x M8 traversants',
         font_size='9px', fill='#555')

    dwg.save()
    print(f"  {dwg.filename}")


# =============================================================================
# 3. BRAS (vue de dessus + coupe extremite)
# =============================================================================
def plan_bras():
    S = 0.8
    W, H = 900, 500
    dwg = new_dwg('bras.svg', W, H)

    title(dwg, W/2, 25, 'BRAS ARTICULES (x4: 2 longs + 2 courts)')

    for i, (length, name, color, y_off) in enumerate([
        (L1, 'Bras 1 (A-a)', '#c62828', 100),
        (L2, 'Bras 2 (B-b)', '#1565c0', 300),
    ]):
        subtitle(dwg, W/2, y_off - 15, f'{name}: L entraxe = {length:.0f}mm | Tube rect {BRAS_TUBE[0]}x{BRAS_TUBE[1]}x{BRAS_TUBE[2]}')

        ox = 80
        oy = y_off + 40

        total_l = (length + 40) * S  # longueur totale avec depassement
        tube_h = BRAS_TUBE[1] * S

        # Tube principal
        rect(dwg, ox + 20*S, oy - tube_h/2, length*S, tube_h,
             fill='#e0e0e0', stroke=color, stroke_width=1.5)

        # Plats d'extremite
        plat_w = PLAT_EXT[0] * S
        plat_h = PLAT_EXT[1] * S
        # Gauche
        rect(dwg, ox, oy - plat_h/2, plat_w/2 + 20*S, plat_h,
             fill='#ccc', stroke=color, stroke_width=1)
        circle(dwg, ox + 20*S, oy, BAGUE[1]/2*S, fill='white', stroke=color, stroke_width=1.5)
        circle(dwg, ox + 20*S, oy, BAGUE[0]/2*S, fill='white', stroke=color, stroke_width=0.8)
        # Droite
        rect(dwg, ox + (length-20)*S, oy - plat_h/2, plat_w/2 + 20*S, plat_h,
             fill='#ccc', stroke=color, stroke_width=1)
        circle(dwg, ox + length*S, oy, BAGUE[1]/2*S, fill='white', stroke=color, stroke_width=1.5)
        circle(dwg, ox + length*S, oy, BAGUE[0]/2*S, fill='white', stroke=color, stroke_width=0.8)

        # Cotes
        dim_h(dwg, ox + 20*S, ox + length*S, oy + plat_h/2 + 20,
              f'entraxe {length:.0f}mm', gap=10)

        # Labels pivots
        text(dwg, ox + 20*S, oy - plat_h/2 - 8,
             'Pivot mur' if i == 0 else 'Pivot mur', font_size='8px', fill=color)
        text(dwg, ox + length*S, oy - plat_h/2 - 8,
             'Pivot porte' if i == 0 else 'Pivot porte', font_size='8px', fill=color)

        # Detail bague
        text(dwg, ox + length*S + 50, oy,
             f'Bague {BAGUE[0]}x{BAGUE[1]}x{BAGUE[2]}mm', font_size='7px', fill='#555', text_anchor='start')

    # Materiel
    text(dwg, W/2, H - 15,
         f'Tube rect {BRAS_TUBE[0]}x{BRAS_TUBE[1]}x{BRAS_TUBE[2]} S235 | '
         f'Plats extremite {PLAT_EXT[0]}x{PLAT_EXT[1]}x{PLAT_EXT[2]}mm | '
         f'Bagues iglidur G {BAGUE[0]}x{BAGUE[1]}x{BAGUE[2]}mm',
         font_size='9px', fill='#555')

    dwg.save()
    print(f"  {dwg.filename}")


# =============================================================================
# 4. AXE DE PIVOT
# =============================================================================
def plan_axe():
    S = 3.0
    W, H = 500, 300
    dwg = new_dwg('axe_pivot.svg', W, H)

    title(dwg, W/2, 25, 'AXE DE PIVOT (x8)')
    subtitle(dwg, W/2, 42, f'Inox 304, D{AXE_D}mm, L={AXE_L}mm')

    ox, oy = 100, 150
    l = AXE_L * S
    r = AXE_D / 2 * S

    # Corps de l'axe (rectangle = vue de profil)
    rect(dwg, ox, oy - r, l, AXE_D * S, fill='#e8e8e8', stroke='black', stroke_width=1.5)

    # Gorge circlip (en bas, a 2mm du bout)
    gorge_x = ox + l - 2*S
    gorge_w = 2 * S
    rect(dwg, gorge_x - gorge_w/2, oy - r - 2, gorge_w, AXE_D*S + 4,
         fill='white', stroke='black', stroke_width=0.8)
    text(dwg, gorge_x, oy + r + 15, 'gorge\ncirclip E16', font_size='7px', fill='#555')

    # Trou goupille fendue (en haut, a 5mm du bout)
    trou_x = ox + 5*S
    circle(dwg, trou_x, oy, 1.5*S, fill='white', stroke='black', stroke_width=0.8)
    text(dwg, trou_x, oy - r - 10, 'trou D3\ngoupille', font_size='7px', fill='#555')

    # Cotes
    dim_h(dwg, ox, ox + l, oy + r + 30, f'{AXE_L}mm', gap=10)
    dim_v(dwg, ox - 20, oy - r, oy + r, f'D{AXE_D}mm', gap=-10)
    dim_h(dwg, gorge_x, ox + l, oy - r - 20, '2mm', gap=8)
    dim_h(dwg, ox, trou_x, oy - r - 35, '5mm', gap=8)

    # Rondelle + empilage
    text(dwg, W/2, H - 40, 'Retention: goupille fendue 3x25mm (haut) + circlip E16 DIN 6799 (bas)',
         font_size='9px', fill='#555')
    text(dwg, W/2, H - 25, 'Rondelles friction: bronze ou nylon D16.5/25 ep.2mm entre chaque piece',
         font_size='9px', fill='#555')

    dwg.save()
    print(f"  {dwg.filename}")


# =============================================================================
# 5. NOMENCLATURE
# =============================================================================
def plan_nomenclature():
    W, H = 900, 500
    dwg = new_dwg('nomenclature.svg', W, H)

    title(dwg, W/2, 25, 'NOMENCLATURE - MECANISME 4-BAR LINKAGE')
    subtitle(dwg, W/2, 42, 'Quantites pour un mecanisme complet (haut + bas)')

    items = [
        ('PM', 'Platine murale monobloc (A+B)', '2', 'Tole S235 6mm pliee+soudee', '200x150mm + montant 107mm'),
        ('PP', 'Platine porte monobloc (a+b)', '2', 'Semelle 8mm + tubes carres', f'Semelle {ENTRAXE_PORTE_X+80:.0f}x{SEMELLE_W}mm'),
        ('BR1', f'Bras 1 (long)', '2', f'Tube rect {BRAS_TUBE[0]}x{BRAS_TUBE[1]}x{BRAS_TUBE[2]}', f'L entraxe = {L1:.0f}mm'),
        ('BR2', f'Bras 2 (court)', '2', f'Tube rect {BRAS_TUBE[0]}x{BRAS_TUBE[1]}x{BRAS_TUBE[2]}', f'L entraxe = {L2:.0f}mm'),
        ('AX', 'Axe pivot', '8', f'Rond inox 304 D{AXE_D}mm', f'L={AXE_L}mm + gorge + trou'),
        ('BG', 'Bague palier', '16', f'Iglidur G ou bronze CuSn8', f'{BAGUE[0]}x{BAGUE[1]}x{BAGUE[2]}mm'),
        ('RO', 'Rondelle friction', '16', 'Bronze ou nylon', 'D16.5/25 ep.2mm'),
        ('CL', 'Circlip E16', '8', 'Acier ressort DIN 6799', ''),
        ('GP', 'Goupille fendue', '8', 'Inox', '3x25mm'),
        ('CH', 'Cheville chimique M12', '8', 'Fischer FIS V ou equiv.', 'Prof. ancrage 100mm'),
        ('BL', 'Boulon traversant M8x60', '24', 'Classe 8.8 + Nylstop', ''),
        ('CP', 'Contre-plaque interieure', '4', 'Tole acier 3mm', '~120x80mm'),
        ('BT', 'Butee reglable', '2', 'Boulon M12x40 + contre-ecrou', '+ tampon EPDM 5mm'),
    ]

    # En-tete
    y = 65
    cols = [30, 80, 380, 420, 560, 750]
    headers = ['Ref', 'Description', 'Qte', 'Materiel', 'Dimensions']
    for c, h in zip(cols, headers):
        text(dwg, c, y, h, font_size='9px', font_weight='bold', text_anchor='start')
    y += 5
    line(dwg, 20, y, W-20, y, stroke='black', stroke_width=1)

    for ref, desc, qty, mat, dims in items:
        y += 18
        for c, val in zip(cols, [ref, desc, qty, mat, dims]):
            text(dwg, c, y, val, font_size='8px', text_anchor='start')

    y += 10
    line(dwg, 20, y, W-20, y, stroke='black', stroke_width=0.5)

    text(dwg, W/2, H - 15, 'Traitement surface: galvanisation a chaud ou peinture epoxy 2 composants',
         font_size='9px', fill='#555')

    dwg.save()
    print(f"  {dwg.filename}")


# =============================================================================
if __name__ == '__main__':
    print("Generation des plans charnieres SVG...")
    plan_platine_murale()
    plan_platine_porte()
    plan_bras()
    plan_axe()
    plan_nomenclature()
    print(f"\nOuvrir dans le navigateur:")
    for f in ['platine_murale.svg', 'platine_porte.svg', 'bras.svg', 'axe_pivot.svg', 'nomenclature.svg']:
        print(f"  file://{os.path.join(outdir, f)}")
