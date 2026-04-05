#!/usr/bin/env python3
"""
Generation des plans techniques cotes en SVG.
Plan 1: Vue de dessus avec mecanisme et cotes
Plan 2: Detail de la porte trapeze avec etageres
"""
import numpy as np
import svgwrite
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'calculs'))
from optimisation_documentee import (
    OW, DT, DW, LWD, RWD, SBR, EFF_BACK,
    CADRE_HINGE, CADRE_TRAILING, TAPER_HINGE, TAPER_TRAILING,
    coins_porte
)

# Parametres de la solution
Ax, Ay = 1237.7, 427.9
Bx, By = 1188.4, 531.6
ax_d, ay_d = 563.3, 450.2
bx_d, by_d = 742.7, 543.8
L1 = np.sqrt((Ax-ax_d)**2 + (Ay-ay_d)**2)
L2 = np.sqrt((Bx-bx_d)**2 + (By-by_d)**2)

CORN = coins_porte()
outdir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'exports')
os.makedirs(outdir, exist_ok=True)

# =============================================================================
# Utilitaires SVG
# =============================================================================
SCALE = 0.5  # 1mm reel = 0.5px SVG (echelle 1:2 sur ecran)
MARGIN = 80  # marge en px

def to_svg(x, y):
    """Convertit coords reelles (mm) en coords SVG (y inverse)."""
    return (x * SCALE + MARGIN, (-y) * SCALE + 500)

def add_line(dwg, x1, y1, x2, y2, **kwargs):
    p1 = to_svg(x1, y1)
    p2 = to_svg(x2, y2)
    dwg.add(dwg.line(start=p1, end=p2, **kwargs))

def add_rect_world(dwg, x, y, w, h, **kwargs):
    """Rectangle en coords monde."""
    p = to_svg(x, y + h)  # SVG y inverse
    dwg.add(dwg.rect(insert=p, size=(w*SCALE, h*SCALE), **kwargs))

def add_polygon(dwg, pts_world, **kwargs):
    svg_pts = [to_svg(x, y) for x, y in pts_world]
    dwg.add(dwg.polygon(points=svg_pts, **kwargs))

def add_circle(dwg, x, y, r, **kwargs):
    dwg.add(dwg.circle(center=to_svg(x, y), r=r, **kwargs))

def add_text(dwg, x, y, text, **kwargs):
    p = to_svg(x, y)
    defaults = {'font_size': '11px', 'font_family': 'Arial', 'text_anchor': 'middle'}
    defaults.update(kwargs)
    dwg.add(dwg.text(text, insert=p, **defaults))

def add_dim_h(dwg, x1, x2, y, text, offset=25):
    """Cote horizontale."""
    y_line = y - offset
    add_line(dwg, x1, y_line, x2, y_line, stroke='black', stroke_width=0.5)
    add_line(dwg, x1, y-5, x1, y_line-5, stroke='black', stroke_width=0.3)
    add_line(dwg, x2, y-5, x2, y_line-5, stroke='black', stroke_width=0.3)
    # Fleches
    for xx, d in [(x1, 4), (x2, -4)]:
        add_line(dwg, xx, y_line, xx+d, y_line+2, stroke='black', stroke_width=0.5)
        add_line(dwg, xx, y_line, xx+d, y_line-2, stroke='black', stroke_width=0.5)
    add_text(dwg, (x1+x2)/2, y_line+3, text, font_size='10px')

def add_dim_v(dwg, x, y1, y2, text, offset=25):
    """Cote verticale."""
    x_line = x + offset
    add_line(dwg, x_line, y1, x_line, y2, stroke='black', stroke_width=0.5)
    add_line(dwg, x+5, y1, x_line+5, y1, stroke='black', stroke_width=0.3)
    add_line(dwg, x+5, y2, x_line+5, y2, stroke='black', stroke_width=0.3)
    p = to_svg(x_line+3, (y1+y2)/2)
    dwg.add(dwg.text(text, insert=p, font_size='10px', font_family='Arial',
                      transform=f'rotate(-90,{p[0]},{p[1]})'))


# =============================================================================
# PLAN 1: Vue de dessus - Mecanisme complet
# =============================================================================
def plan_vue_dessus():
    w = int((OW + EFF_BACK + 400) * SCALE + 2 * MARGIN)
    h = int(800 * SCALE + 2 * MARGIN)
    dwg = svgwrite.Drawing(os.path.join(outdir, 'plan_vue_dessus.svg'),
                           size=(f'{w}px', f'{h}px'))

    # Titre
    dwg.add(dwg.text('VUE DE DESSUS - Mecanisme 4-bar linkage',
                      insert=(w/2, 20), font_size='16px', font_family='Arial',
                      text_anchor='middle', font_weight='bold'))
    dwg.add(dwg.text(f'Porte {DW}x{DT}mm trapeze | Cadres {CADRE_TRAILING}/{CADRE_HINGE}mm | Echelle ~1:2',
                      insert=(w/2, 38), font_size='11px', font_family='Arial',
                      text_anchor='middle', fill='gray'))

    # Mur gauche (trailing)
    add_rect_world(dwg, -250, 0, 250, LWD,
                   fill='#d0d0d0', stroke='black', stroke_width=1)
    add_text(dwg, -125, LWD/2, 'MUR GAUCHE', font_size='9px', fill='#555')
    add_text(dwg, -125, LWD/2 - 20, f'{LWD}mm', font_size='8px', fill='#555')

    # Mur droit (charnieres)
    add_rect_world(dwg, OW, 0, EFF_BACK + 80, RWD,
                   fill='#d0d0d0', stroke='black', stroke_width=1)
    add_text(dwg, OW + 100, RWD/2, 'MUR DROIT', font_size='9px', fill='#555')
    add_text(dwg, OW + 100, RWD/2 - 20, f'{RWD}mm', font_size='8px', fill='#555')

    # Limite frigo
    add_line(dwg, OW + SBR, 0, OW + SBR, 700,
             stroke='red', stroke_width=1, stroke_dasharray='5,3')
    add_text(dwg, OW + SBR + 10, 650, 'FRIGO', font_size='9px', fill='red',
             text_anchor='start')

    # Cadres
    if CADRE_TRAILING > 0:
        add_rect_world(dwg, 0, 0, CADRE_TRAILING, DT,
                       fill='#8d6e63', fill_opacity=0.4, stroke='black', stroke_width=0.5)
    if CADRE_HINGE > 0:
        add_rect_world(dwg, OW - CADRE_HINGE, 0, CADRE_HINGE, DT,
                       fill='#8d6e63', fill_opacity=0.4, stroke='black', stroke_width=0.5)

    # Porte fermee (trapeze)
    add_polygon(dwg, CORN, fill='#a5d6a7', fill_opacity=0.5,
                stroke='#2e7d32', stroke_width=1.5)
    add_text(dwg, (CORN[0,0]+CORN[3,0])/2, DT/2, 'PORTE (fermee)',
             font_size='10px', fill='#2e7d32')

    # Labels coins
    for i, (name, color) in enumerate(zip(['C1','C2','C3','C4'],
                                           ['red','blue','green','orange'])):
        add_circle(dwg, CORN[i,0], CORN[i,1], 3, fill=color)
        ox = -15 if i < 2 else 15
        oy = -10 if i % 3 == 0 else 10
        add_text(dwg, CORN[i,0]+ox, CORN[i,1]+oy, name,
                 font_size='9px', fill=color, font_weight='bold')

    # Pivots sur pattes
    add_circle(dwg, ax_d, ay_d, 4, fill='red', stroke='black', stroke_width=1)
    add_text(dwg, ax_d, ay_d + 20, f'a ({ax_d:.0f},{ay_d:.0f})',
             font_size='8px', fill='red')
    add_circle(dwg, bx_d, by_d, 4, fill='blue', stroke='black', stroke_width=1)
    add_text(dwg, bx_d, by_d + 20, f'b ({bx_d:.0f},{by_d:.0f})',
             font_size='8px', fill='blue')

    # Pattes (lignes tiretees de la face arriere aux pivots)
    # Patte a: du point (ax_d, DT) sur la face arriere au pivot (ax_d, ay_d)
    add_line(dwg, ax_d, DT, ax_d, ay_d,
             stroke='red', stroke_width=1, stroke_dasharray='3,2')
    # Patte b
    add_line(dwg, bx_d, DT, bx_d, by_d,
             stroke='blue', stroke_width=1, stroke_dasharray='3,2')

    # Pivots mur
    add_circle(dwg, Ax, Ay, 5, fill='red', stroke='black', stroke_width=1.5)
    add_text(dwg, Ax - 30, Ay, f'A ({Ax:.0f},{Ay:.0f})',
             font_size='9px', fill='red', font_weight='bold')
    add_circle(dwg, Bx, By, 5, fill='blue', stroke='black', stroke_width=1.5)
    add_text(dwg, Bx - 30, By, f'B ({Bx:.0f},{By:.0f})',
             font_size='9px', fill='blue', font_weight='bold')

    # Bras (position fermee)
    add_line(dwg, Ax, Ay, ax_d, ay_d,
             stroke='red', stroke_width=2, stroke_opacity=0.6)
    add_text(dwg, (Ax+ax_d)/2, (Ay+ay_d)/2 - 10, f'Bras 1: {L1:.0f}mm',
             font_size='9px', fill='red')
    add_line(dwg, Bx, By, bx_d, by_d,
             stroke='blue', stroke_width=2, stroke_opacity=0.6)
    add_text(dwg, (Bx+bx_d)/2, (By+by_d)/2 + 15, f'Bras 2: {L2:.0f}mm',
             font_size='9px', fill='blue')

    # Cotes
    add_dim_h(dwg, 0, OW, -10, f'{OW}mm', offset=30)
    add_dim_h(dwg, CORN[0,0], CORN[3,0], -10, f'{DW}mm', offset=55)
    add_dim_v(dwg, -30, 0, DT, f'{DT}mm', offset=-50)
    add_dim_v(dwg, OW + 30, 0, RWD, f'{RWD}mm', offset=50)
    add_dim_h(dwg, OW, OW + SBR, RWD + 20, f'{SBR}mm', offset=20)

    # Zones
    add_text(dwg, OW/2, -40, 'CUISINE', font_size='14px', fill='#c65100',
             font_weight='bold')
    add_text(dwg, OW/2, 650, 'BUANDERIE', font_size='14px', fill='#1565c0',
             font_weight='bold')

    dwg.save()
    print(f"  Saved: {dwg.filename}")


# =============================================================================
# PLAN 2: Detail porte trapeze
# =============================================================================
def plan_porte_detail():
    # Dessiner la porte seule avec cotes et etageres
    # Coords locales de la porte (C1 a l'origine)
    c1 = CORN[0]
    c2 = CORN[1]
    c3 = CORN[2]
    c4 = CORN[3]

    w = int(900 * SCALE + 2 * MARGIN)
    h = int(600 * SCALE + 2 * MARGIN)
    dwg = svgwrite.Drawing(os.path.join(outdir, 'plan_porte_detail.svg'),
                           size=(f'{w}px', f'{h}px'))

    # Titre
    dwg.add(dwg.text('DETAIL PORTE TRAPEZE + ETAGERES',
                      insert=(w/2, 20), font_size='16px', font_family='Arial',
                      text_anchor='middle', font_weight='bold'))
    dwg.add(dwg.text(f'{DW}x{DT}mm | Taper {TAPER_HINGE}/{TAPER_TRAILING}mm | Echelle ~1:2',
                      insert=(w/2, 38), font_size='11px', font_family='Arial',
                      text_anchor='middle', fill='gray'))

    # Porte (trapeze)
    add_polygon(dwg, CORN, fill='#fff9c4', stroke='black', stroke_width=2)

    # Face cuisine (bas)
    add_text(dwg, (c1[0]+c4[0])/2, c1[1]-15, 'Face CUISINE (visible)',
             font_size='10px', fill='#c65100')
    # Face buanderie (haut)
    add_text(dwg, (c2[0]+c3[0])/2, c2[1]+25, 'Face BUANDERIE (etageres)',
             font_size='10px', fill='#1565c0')

    # Etageres (3 niveaux, entre les aretes C1-C2 et C4-C3)
    for i, frac in enumerate([0.25, 0.5, 0.75]):
        p1 = c1 * (1-frac) + c2 * frac
        p2 = c4 * (1-frac) + c3 * frac
        add_line(dwg, p1[0]+10, p1[1], p2[0]-10, p2[1],
                 stroke='#795548', stroke_width=1.5, stroke_dasharray='8,3')
        add_text(dwg, (p1[0]+p2[0])/2, p1[1]-8, f'Etagere {i+1} (y={p1[1]:.0f}mm)',
                 font_size='8px', fill='#795548')

    # Coins
    for i, (name, color) in enumerate(zip(['C1','C2','C3','C4'],
                                           ['red','blue','green','orange'])):
        add_circle(dwg, CORN[i,0], CORN[i,1], 3, fill=color)
        ox = -20 if i < 2 else 20
        oy = -12 if i in [0,3] else 12
        add_text(dwg, CORN[i,0]+ox, CORN[i,1]+oy,
                 f'{name} ({CORN[i,0]:.0f},{CORN[i,1]:.0f})',
                 font_size='8px', fill=color, font_weight='bold')

    # Pivots (pattes)
    add_circle(dwg, ax_d, ay_d, 4, fill='red', stroke='black')
    add_line(dwg, ax_d, DT, ax_d, ay_d, stroke='red', stroke_width=1.5,
             stroke_dasharray='3,2')
    add_text(dwg, ax_d-5, ay_d+15, f'Pivot a\npatte {ay_d-DT:.0f}mm',
             font_size='8px', fill='red')

    add_circle(dwg, bx_d, by_d, 4, fill='blue', stroke='black')
    add_line(dwg, bx_d, DT, bx_d, by_d, stroke='blue', stroke_width=1.5,
             stroke_dasharray='3,2')
    add_text(dwg, bx_d+5, by_d+15, f'Pivot b\npatte {by_d-DT:.0f}mm',
             font_size='8px', fill='blue')

    # Cotes
    add_dim_h(dwg, c1[0], c4[0], c1[1], f'{c4[0]-c1[0]:.0f}mm (cuisine)', offset=40)
    add_dim_h(dwg, c2[0], c3[0], c2[1], f'{c3[0]-c2[0]:.0f}mm (buanderie)', offset=-30)
    add_dim_v(dwg, c1[0]-10, c1[1], c2[1], f'{DT}mm', offset=-40)
    add_dim_h(dwg, c1[0], c2[0], (c1[1]+c2[1])/2, f'taper {TAPER_TRAILING}mm', offset=-10)
    add_dim_h(dwg, c3[0], c4[0], (c3[1]+c4[1])/2, f'taper {TAPER_HINGE}mm', offset=-10)

    dwg.save()
    print(f"  Saved: {dwg.filename}")


# =============================================================================
if __name__ == '__main__':
    print("Generation des plans SVG...")
    plan_vue_dessus()
    plan_porte_detail()
    print("\nOuvrir dans un navigateur:")
    print(f"  file://{os.path.join(outdir, 'plan_vue_dessus.svg')}")
    print(f"  file://{os.path.join(outdir, 'plan_porte_detail.svg')}")
