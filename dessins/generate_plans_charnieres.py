#!/usr/bin/env python3
"""
Dessins techniques cotes des pieces de charniere (4-bar linkage).
Design simplifie: tole pliee 3 faces (fond+plat+cote) avec 2 pivots par platine.

Genere des SVG pour:
1. Platine murale combinee (A+B) — patron deplie + profil plie
2. Platine porte combinee (a+b) — patron deplie + profil plie
3. Bras (2 types: long + court) — tubes rectangulaires simples
4. Nomenclature (bill of materials)
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
L1 = math.sqrt((Ax - ax_d)**2 + (Ay - ay_d)**2)  # ~584mm
L2 = math.sqrt((Bx - bx_d)**2 + (By - by_d)**2)  # ~425mm

# Profondeurs pivots depuis mur/porte
DEPTH_A_MUR = Ay - RWD       # 46mm (pivot A depuis face mur)
DEPTH_B_MUR = By - RWD       # 161mm (pivot B depuis face mur)
DEPTH_A_PORTE = ay_d - DT    # 71mm (pivot a depuis face porte)
DEPTH_B_PORTE = by_d - DT    # 186mm (pivot b depuis face porte)

# Entraxes X entre pivots
ENTRAXE_MUR_X = abs(Ax - Bx)    # 57.7mm
ENTRAXE_PORTE_X = abs(bx_d - ax_d)  # 102.1mm

# Dimensions des pieces
TOLE = 5          # epaisseur tole platines (mm)
AXE_D = 16        # diametre axe/boulon pivot
AXE_HOLE = 18     # diametre percage pour axe
BRAS_TUBE = (40, 25, 3)  # tube rect: largeur, hauteur, epaisseur

# Platine murale
MUR_WIDTH = 138       # largeur platine (57.7 + 2x40 margin)
MUR_PLAT_DEPTH = 185  # profondeur plat (161 + 24 margin)
MUR_FOND_H = 150      # hauteur fond (sur le mur)
MUR_COTE_DEPTH = 73   # profondeur du cote (rabat raidisseur)
MUR_HOLE_A_X = 29     # offset X du trou A depuis centre (+29 = vers Ax plus grand)
MUR_HOLE_B_X = -29    # offset X du trou B depuis centre (-29 = vers Bx plus petit)
MUR_HOLE_A_Y = 46     # profondeur trou A depuis fond
MUR_HOLE_B_Y = 161    # profondeur trou B depuis fond

# Platine porte
PORTE_WIDTH = 182      # largeur platine (102.1 + 2x40 margin)
PORTE_PLAT_DEPTH = 210 # profondeur plat (186 + 24 margin)
PORTE_FOND_H = 150     # hauteur fond (sur la porte)
PORTE_COTE_DEPTH = 73  # profondeur du cote
PORTE_HOLE_A_X = -51   # offset X du trou a depuis centre
PORTE_HOLE_B_X = 51    # offset X du trou b depuis centre
PORTE_HOLE_A_Y = 71    # profondeur trou a depuis fond
PORTE_HOLE_B_Y = 186   # profondeur trou b depuis fond

# Boulon pivot
AXE_L = 45  # longueur boulon (~tole 5 + tube 25 + rondelles + ecrou)

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
    dwg.add(dwg.line(start=(x1, y1), end=(x2, y2), **kw))

def rect(dwg, x, y, w, h, **kw):
    kw.setdefault('stroke', 'black')
    kw.setdefault('stroke_width', 1)
    kw.setdefault('fill', 'none')
    dwg.add(dwg.rect(insert=(x, y), size=(w, h), **kw))

def circle(dwg, cx, cy, r, **kw):
    kw.setdefault('stroke', 'black')
    kw.setdefault('stroke_width', 1)
    kw.setdefault('fill', 'none')
    dwg.add(dwg.circle(center=(cx, cy), r=r, **kw))

def text(dwg, x, y, txt, **kw):
    kw.setdefault('font_size', '10px')
    kw.setdefault('font_family', 'Arial')
    kw.setdefault('text_anchor', 'middle')
    dwg.add(dwg.text(txt, insert=(x, y), **kw))

def dim_h(dwg, x1, x2, y, label, gap=15):
    """Cote horizontale avec fleches."""
    line(dwg, x1, y, x2, y, stroke='#333', stroke_width=0.5)
    line(dwg, x1, y - gap, x1, y + 5, stroke='#333', stroke_width=0.3)
    line(dwg, x2, y - gap, x2, y + 5, stroke='#333', stroke_width=0.3)
    for xx, d in [(x1, 3), (x2, -3)]:
        line(dwg, xx, y, xx + d, y - 2, stroke='#333', stroke_width=0.5)
        line(dwg, xx, y, xx + d, y + 2, stroke='#333', stroke_width=0.5)
    text(dwg, (x1 + x2) / 2, y - 3, label, font_size='9px', fill='#333')

def dim_v(dwg, x, y1, y2, label, gap=15):
    """Cote verticale avec fleches."""
    line(dwg, x, y1, x, y2, stroke='#333', stroke_width=0.5)
    line(dwg, x - 5, y1, x + gap, y1, stroke='#333', stroke_width=0.3)
    line(dwg, x - 5, y2, x + gap, y2, stroke='#333', stroke_width=0.3)
    for yy, d in [(y1, 3), (y2, -3)]:
        line(dwg, x, yy, x - 2, yy + d, stroke='#333', stroke_width=0.5)
        line(dwg, x, yy, x + 2, yy + d, stroke='#333', stroke_width=0.5)
    mid = (y1 + y2) / 2
    dwg.add(dwg.text(label, insert=(x + gap + 2, mid + 3), font_size='9px',
                      font_family='Arial', fill='#333'))

def title(dwg, x, y, txt):
    text(dwg, x, y, txt, font_size='14px', font_weight='bold')

def subtitle(dwg, x, y, txt):
    text(dwg, x, y, txt, font_size='10px', fill='gray')


# =============================================================================
# Patron deplie generique pour platine 3 faces (fond + plat + cote)
# =============================================================================
def _draw_platine_flat(dwg, ox, oy, width, fond_h, plat_depth, cote_depth,
                       hole_a_x, hole_a_y, hole_b_x, hole_b_y,
                       screw_type, screw_positions, label_a, label_b):
    """Dessine le patron deplie d'une platine 3 faces.

    Le patron est dispose verticalement:
      COTE (en haut) | pliage 2 | PLAT (milieu) | pliage 1 | FOND (en bas)

    ox, oy = coin haut-gauche du patron complet.
    Les trous de pivot sont dans la section PLAT.
    Les vis/chevilles sont dans la section FOND.
    """
    total_h = cote_depth + plat_depth + fond_h

    # --- Section COTE (haut) ---
    rect(dwg, ox, oy, width, cote_depth, fill='#e8e8d8', stroke='black', stroke_width=1.5)
    text(dwg, ox + width / 2, oy + cote_depth / 2 + 3,
         f'COTE (raidisseur)', font_size='8px', fill='#777')
    text(dwg, ox + width / 2, oy + cote_depth / 2 + 14,
         f'{width}x{cote_depth}mm', font_size='7px', fill='#999')

    # --- Ligne pliage 2 (entre cote et plat) ---
    pliage2_y = oy + cote_depth
    line(dwg, ox, pliage2_y, ox + width, pliage2_y,
         stroke='#e00', stroke_width=1.5, stroke_dasharray='8,4')
    text(dwg, ox - 5, pliage2_y + 3, 'pliage 2', font_size='8px',
         fill='#e00', text_anchor='end')

    # --- Section PLAT (milieu) ---
    plat_y = pliage2_y
    rect(dwg, ox, plat_y, width, plat_depth, fill='#d0d8e8', stroke='black', stroke_width=1.5)
    text(dwg, ox + width / 2, plat_y + 15,
         f'PLAT (perpendiculaire)', font_size='8px', fill='#555')
    text(dwg, ox + width / 2, plat_y + 27,
         f'{width}x{plat_depth}mm', font_size='7px', fill='#999')

    # Trous pivots dans le PLAT (mesurees depuis le bord fond = bas du plat)
    cx = ox + width / 2
    # Trou A (plus proche du fond)
    hole_a_cx = cx + hole_a_x
    hole_a_cy = plat_y + plat_depth - hole_a_y  # depuis le bas du plat (cote fond)
    circle(dwg, hole_a_cx, hole_a_cy, AXE_HOLE / 2,
           fill='white', stroke='red', stroke_width=2)
    text(dwg, hole_a_cx, hole_a_cy - AXE_HOLE / 2 - 6, label_a,
         font_size='9px', fill='red', font_weight='bold')
    text(dwg, hole_a_cx + AXE_HOLE / 2 + 3, hole_a_cy + 3,
         f'D{AXE_HOLE}', font_size='7px', fill='red', text_anchor='start')

    # Trou B (plus profond)
    hole_b_cx = cx + hole_b_x
    hole_b_cy = plat_y + plat_depth - hole_b_y
    circle(dwg, hole_b_cx, hole_b_cy, AXE_HOLE / 2,
           fill='white', stroke='blue', stroke_width=2)
    text(dwg, hole_b_cx, hole_b_cy - AXE_HOLE / 2 - 6, label_b,
         font_size='9px', fill='blue', font_weight='bold')
    text(dwg, hole_b_cx + AXE_HOLE / 2 + 3, hole_b_cy + 3,
         f'D{AXE_HOLE}', font_size='7px', fill='blue', text_anchor='start')

    # Annotation: direction des boulons
    text(dwg, hole_a_cx - 25, hole_a_cy + 3,
         'boulon vers\nle HAUT', font_size='6px', fill='red', text_anchor='end')
    text(dwg, hole_b_cx - 25, hole_b_cy + 3,
         'boulon vers\nle BAS', font_size='6px', fill='blue', text_anchor='end')

    # --- Ligne pliage 1 (entre plat et fond) ---
    pliage1_y = plat_y + plat_depth
    line(dwg, ox, pliage1_y, ox + width, pliage1_y,
         stroke='#e00', stroke_width=1.5, stroke_dasharray='8,4')
    text(dwg, ox - 5, pliage1_y + 3, 'pliage 1', font_size='8px',
         fill='#e00', text_anchor='end')

    # --- Section FOND (bas) ---
    fond_y = pliage1_y
    rect(dwg, ox, fond_y, width, fond_h, fill='#d8d8d8', stroke='black', stroke_width=1.5)
    text(dwg, ox + width / 2, fond_y + fond_h / 2 - 5,
         f'FOND (contre {screw_type})', font_size='8px', fill='#555')
    text(dwg, ox + width / 2, fond_y + fond_h / 2 + 7,
         f'{width}x{fond_h}mm', font_size='7px', fill='#999')

    # Trous de fixation dans le fond
    for sx, sy in screw_positions:
        scr_cx = cx + sx
        scr_cy = fond_y + fond_h / 2 + sy
        circle(dwg, scr_cx, scr_cy, 5, fill='#555', stroke='black')

    # --- Cotes ---
    # Largeur totale
    dim_h(dwg, ox, ox + width, oy - 20, f'{width}mm', gap=12)
    # Hauteurs des 3 sections (cote droit)
    rx = ox + width + 15
    dim_v(dwg, rx, oy, pliage2_y, f'{cote_depth}mm', gap=10)
    dim_v(dwg, rx, pliage2_y, pliage1_y, f'{plat_depth}mm', gap=10)
    dim_v(dwg, rx, pliage1_y, fond_y + fond_h, f'{fond_h}mm', gap=10)
    # Hauteur totale
    dim_v(dwg, rx + 40, oy, fond_y + fond_h, f'{total_h}mm (total)', gap=10)

    # Cotes des trous pivots (depuis bord fond = pliage 1)
    lx = ox - 15
    dim_v(dwg, lx, pliage1_y, hole_a_cy, f'{hole_a_y}mm', gap=-15)
    dim_v(dwg, lx - 30, pliage1_y, hole_b_cy, f'{hole_b_y}mm', gap=-15)

    # Entraxe X entre pivots
    if hole_a_cx != hole_b_cx:
        dim_h(dwg, min(hole_a_cx, hole_b_cx), max(hole_a_cx, hole_b_cx),
              plat_y - 5, f'{abs(hole_a_x - hole_b_x):.0f}mm', gap=8)

    return total_h


def _draw_platine_folded(dwg, ox, oy, width, fond_h, plat_depth, cote_depth,
                         hole_a_y, hole_b_y, label_a, label_b, surface_label):
    """Dessine la vue de profil de la platine pliee (vue de cote).

    ox, oy = coin bas-gauche du fond (point d'attache sur mur/porte).
    Fond vertical, plat horizontal vers la droite, cote vertical vers le bas.
    """
    S = 0.6  # echelle pour la vue pliee

    # Surface de reference (mur ou porte)
    rect(dwg, ox - 40, oy - fond_h * S, 40, fond_h * S,
         fill='#e8e8e8', stroke='#bbb')
    text(dwg, ox - 20, oy - fond_h * S / 2 + 3, surface_label,
         font_size='7px', fill='#999')

    # FOND (vertical, plaque contre la surface)
    rect(dwg, ox, oy - fond_h * S, TOLE * S, fond_h * S,
         fill='#b0b0b0', stroke='black', stroke_width=2)
    text(dwg, ox + TOLE * S + 8, oy - fond_h * S / 2 + 3,
         'FOND', font_size='7px', fill='#555', text_anchor='start')

    # PLAT (horizontal, perpendiculaire au fond, part du haut du fond)
    plat_x = ox + TOLE * S
    plat_y = oy - fond_h * S
    rect(dwg, plat_x, plat_y, plat_depth * S, TOLE * S,
         fill='#a0a8b8', stroke='black', stroke_width=2)

    # Trous pivots sur le PLAT (vus de profil = traits)
    hole_a_px = plat_x + hole_a_y * S
    hole_b_px = plat_x + hole_b_y * S
    plat_mid = plat_y + TOLE * S / 2
    circle(dwg, hole_a_px, plat_mid, 3, fill='white', stroke='red', stroke_width=1.5)
    text(dwg, hole_a_px, plat_y - 8, label_a, font_size='8px', fill='red', font_weight='bold')
    circle(dwg, hole_b_px, plat_mid, 3, fill='white', stroke='blue', stroke_width=1.5)
    text(dwg, hole_b_px, plat_y - 8, label_b, font_size='8px', fill='blue', font_weight='bold')

    # COTE (vertical, descend depuis l'extremite du plat)
    cote_x = plat_x + plat_depth * S - TOLE * S
    cote_y = plat_y + TOLE * S
    rect(dwg, cote_x, cote_y, TOLE * S, cote_depth * S,
         fill='#c8c8b8', stroke='black', stroke_width=2)
    text(dwg, cote_x + TOLE * S + 8, cote_y + cote_depth * S / 2 + 3,
         'COTE', font_size='7px', fill='#555', text_anchor='start')

    # Soudure (bout du cote au fond)
    # Le cote ne touche pas le fond directement sur la vue, mais l'annotation indique
    # qu'il y a une soudure entre le bout du cote et le fond
    weld_x = ox + TOLE * S / 2
    weld_y = cote_y + cote_depth * S
    line(dwg, cote_x + TOLE * S / 2, weld_y, weld_x, oy,
         stroke='#c00', stroke_width=1, stroke_dasharray='3,3')
    text(dwg, (cote_x + weld_x) / 2, weld_y + 15,
         '1 soudure\n(cote -> fond)', font_size='7px', fill='#c00')

    # Annotations pliages
    text(dwg, ox + TOLE * S / 2, plat_y - 15, 'pliage 1',
         font_size='7px', fill='#e00')
    text(dwg, cote_x, plat_y - 15, 'pliage 2',
         font_size='7px', fill='#e00')

    # Cotes
    dim_h(dwg, plat_x, plat_x + plat_depth * S, plat_y + TOLE * S + 15,
          f'{plat_depth}mm', gap=8)
    dim_v(dwg, ox - 10, oy - fond_h * S, oy, f'{fond_h}mm', gap=-10)
    dim_v(dwg, cote_x + TOLE * S + 25, cote_y, cote_y + cote_depth * S,
          f'{cote_depth}mm', gap=10)


# =============================================================================
# 1. PLATINE MURALE COMBINEE (A+B)
# =============================================================================
def plan_platine_murale():
    W, H = 1100, 850
    dwg = new_dwg('platine_murale.svg', W, H)

    title(dwg, W / 2, 25, 'PLATINE MURALE COMBINEE A+B (x2: haut + bas)')
    subtitle(dwg, W / 2, 42,
             f'Tole acier S235 ep.{TOLE}mm, 2 pliages 90 deg + 1 soudure')

    # --- Vue 1: PATRON DEPLIE ---
    text(dwg, 250, 75, '1. PATRON DEPLIE (avant pliage)',
         font_size='12px', font_weight='bold')
    subtitle(dwg, 250, 90,
             'Decouper + percer, puis plier aux lignes rouges')

    ox1, oy1 = 100, 120

    # Positions des vis de fixation M12 dans le fond (6 trous)
    # 2 colonnes x 3 rangees, espaces regulierement
    screw_pos = []
    for sx in [-30, 30]:
        for sy in [-40, 0, 40]:
            screw_pos.append((sx, sy))

    _draw_platine_flat(dwg, ox1, oy1,
                       MUR_WIDTH, MUR_FOND_H, MUR_PLAT_DEPTH, MUR_COTE_DEPTH,
                       MUR_HOLE_A_X, MUR_HOLE_A_Y,
                       MUR_HOLE_B_X, MUR_HOLE_B_Y,
                       'mur', screw_pos, 'A', 'B')

    # Label vis
    text(dwg, ox1 + MUR_WIDTH / 2, oy1 + MUR_COTE_DEPTH + MUR_PLAT_DEPTH + MUR_FOND_H + 20,
         '6x chevilles chimiques M12', font_size='8px', fill='#555')

    # --- Vue 2: PROFIL PLIE ---
    text(dwg, 750, 75, '2. PROFIL PLIE (vue de cote)',
         font_size='12px', font_weight='bold')
    subtitle(dwg, 750, 90, 'Piece apres pliage, vue depuis le cote')

    _draw_platine_folded(dwg, 620, 650,
                         MUR_WIDTH, MUR_FOND_H, MUR_PLAT_DEPTH, MUR_COTE_DEPTH,
                         MUR_HOLE_A_Y, MUR_HOLE_B_Y,
                         'A', 'B', 'MUR')

    # Notes en bas
    text(dwg, W / 2, H - 45,
         f'Tole S235 ep.{TOLE}mm | 2 pliages 90 deg | 1 soudure (bout cote sur fond)',
         font_size='9px', fill='#555')
    text(dwg, W / 2, H - 30,
         f'Pivot A: boulon D{AXE_D}mm vers le HAUT (bras au-dessus du plat) | '
         f'Pivot B: boulon D{AXE_D}mm vers le BAS (bras en-dessous)',
         font_size='9px', fill='#555')
    text(dwg, W / 2, H - 15,
         f'Fixation mur: 6x chevilles chimiques M12 dans le fond',
         font_size='9px', fill='#555')

    dwg.save()
    print(f"  {dwg.filename}")


# =============================================================================
# 2. PLATINE PORTE COMBINEE (a+b)
# =============================================================================
def plan_platine_porte():
    W, H = 1100, 900
    dwg = new_dwg('platine_porte.svg', W, H)

    title(dwg, W / 2, 25, 'PLATINE PORTE COMBINEE a+b (x2: haut + bas)')
    subtitle(dwg, W / 2, 42,
             f'Tole acier S235 ep.{TOLE}mm, 2 pliages 90 deg + 1 soudure')

    # --- Vue 1: PATRON DEPLIE ---
    text(dwg, 280, 75, '1. PATRON DEPLIE (avant pliage)',
         font_size='12px', font_weight='bold')
    subtitle(dwg, 280, 90,
             'Decouper + percer, puis plier aux lignes rouges')

    ox1, oy1 = 100, 120

    # Positions des boulons traversants M8 dans le fond (6 trous)
    screw_pos = []
    for sx in [-40, 0, 40]:
        for sy in [-40, 0, 40]:
            screw_pos.append((sx, sy))

    _draw_platine_flat(dwg, ox1, oy1,
                       PORTE_WIDTH, PORTE_FOND_H, PORTE_PLAT_DEPTH, PORTE_COTE_DEPTH,
                       PORTE_HOLE_A_X, PORTE_HOLE_A_Y,
                       PORTE_HOLE_B_X, PORTE_HOLE_B_Y,
                       'porte', screw_pos, 'a', 'b')

    # Label vis
    text(dwg, ox1 + PORTE_WIDTH / 2,
         oy1 + PORTE_COTE_DEPTH + PORTE_PLAT_DEPTH + PORTE_FOND_H + 20,
         'Boulons traversants M8 (fond -> porte)', font_size='8px', fill='#555')

    # --- Vue 2: PROFIL PLIE ---
    text(dwg, 780, 75, '2. PROFIL PLIE (vue de cote)',
         font_size='12px', font_weight='bold')
    subtitle(dwg, 780, 90, 'Piece apres pliage, vue depuis le cote')

    _draw_platine_folded(dwg, 650, 700,
                         PORTE_WIDTH, PORTE_FOND_H, PORTE_PLAT_DEPTH, PORTE_COTE_DEPTH,
                         PORTE_HOLE_A_Y, PORTE_HOLE_B_Y,
                         'a', 'b', 'PORTE')

    # Notes en bas
    text(dwg, W / 2, H - 45,
         f'Tole S235 ep.{TOLE}mm | 2 pliages 90 deg | 1 soudure (bout cote sur fond)',
         font_size='9px', fill='#555')
    text(dwg, W / 2, H - 30,
         f'Pivot a: boulon D{AXE_D}mm vers le HAUT (bras au-dessus du plat) | '
         f'Pivot b: boulon D{AXE_D}mm vers le BAS (bras en-dessous)',
         font_size='9px', fill='#555')
    text(dwg, W / 2, H - 15,
         f'Fixation porte: boulons traversants M8 dans le fond',
         font_size='9px', fill='#555')

    dwg.save()
    print(f"  {dwg.filename}")


# =============================================================================
# 3. BRAS (tubes rectangulaires simples)
# =============================================================================
def plan_bras():
    W, H = 900, 500
    dwg = new_dwg('bras.svg', W, H)

    title(dwg, W / 2, 25, 'BRAS ARTICULES (x4: 2 longs + 2 courts)')
    subtitle(dwg, W / 2, 42,
             f'Tube rectangulaire {BRAS_TUBE[0]}x{BRAS_TUBE[1]}x{BRAS_TUBE[2]}mm acier S235')

    S = 0.8

    for i, (length, name, color, y_off, piv_mur, piv_porte) in enumerate([
        (L1, 'Bras 1 (A -> a)', '#c62828', 110, 'A', 'a'),
        (L2, 'Bras 2 (B -> b)', '#1565c0', 310, 'B', 'b'),
    ]):
        entraxe = round(length)
        subtitle(dwg, W / 2, y_off - 10,
                 f'{name}: entraxe = {entraxe}mm | '
                 f'Tube {BRAS_TUBE[0]}x{BRAS_TUBE[1]}x{BRAS_TUBE[2]}')

        ox = 100
        oy = y_off + 50
        tube_w = entraxe * S
        tube_h = BRAS_TUBE[1] * S

        # Tube principal
        rect(dwg, ox, oy - tube_h / 2, tube_w, tube_h,
             fill='#e0e0e0', stroke=color, stroke_width=1.5)
        text(dwg, ox + tube_w / 2, oy + 3,
             f'Tube {BRAS_TUBE[0]}x{BRAS_TUBE[1]}x{BRAS_TUBE[2]}',
             font_size='7px', fill='#888')

        # Trou gauche (pivot mur)
        circle(dwg, ox, oy, AXE_HOLE / 2 * S,
               fill='white', stroke=color, stroke_width=2)
        text(dwg, ox, oy - tube_h / 2 - 12,
             f'Pivot {piv_mur}', font_size='8px', fill=color, font_weight='bold')
        text(dwg, ox, oy - tube_h / 2 - 3,
             f'D{AXE_HOLE}', font_size='7px', fill=color)

        # Trou droit (pivot porte)
        circle(dwg, ox + tube_w, oy, AXE_HOLE / 2 * S,
               fill='white', stroke=color, stroke_width=2)
        text(dwg, ox + tube_w, oy - tube_h / 2 - 12,
             f'Pivot {piv_porte}', font_size='8px', fill=color, font_weight='bold')
        text(dwg, ox + tube_w, oy - tube_h / 2 - 3,
             f'D{AXE_HOLE}', font_size='7px', fill=color)

        # Cote entraxe
        dim_h(dwg, ox, ox + tube_w, oy + tube_h / 2 + 20,
              f'entraxe {entraxe}mm', gap=10)

        # Cote section transversale (petite vue en coupe a droite)
        cx_sec = ox + tube_w + 80
        cy_sec = oy
        sec_w = BRAS_TUBE[0] * S
        sec_h = BRAS_TUBE[1] * S
        ep = BRAS_TUBE[2] * S
        # Tube exterieur
        rect(dwg, cx_sec - sec_w / 2, cy_sec - sec_h / 2, sec_w, sec_h,
             fill='#e0e0e0', stroke=color, stroke_width=1)
        # Creux interieur
        rect(dwg, cx_sec - sec_w / 2 + ep, cy_sec - sec_h / 2 + ep,
             sec_w - 2 * ep, sec_h - 2 * ep,
             fill='white', stroke=color, stroke_width=0.5)
        # Trou pivot
        circle(dwg, cx_sec, cy_sec, AXE_HOLE / 2 * S,
               fill='white', stroke=color, stroke_width=1)
        text(dwg, cx_sec, cy_sec + sec_h / 2 + 15,
             'section', font_size='7px', fill='#888')

    # Notes
    text(dwg, W / 2, H - 30,
         f'Tube rectangulaire {BRAS_TUBE[0]}x{BRAS_TUBE[1]}x{BRAS_TUBE[2]}mm acier S235',
         font_size='9px', fill='#555')
    text(dwg, W / 2, H - 15,
         f'Percages D{AXE_HOLE}mm a chaque extremite pour boulon D{AXE_D}mm | '
         f'Pas de plats d\'extremite ni bagues — boulon direct dans le tube',
         font_size='9px', fill='#555')

    dwg.save()
    print(f"  {dwg.filename}")


# =============================================================================
# 4. NOMENCLATURE
# =============================================================================
def plan_nomenclature():
    W, H = 900, 400
    dwg = new_dwg('nomenclature.svg', W, H)

    title(dwg, W / 2, 25, 'NOMENCLATURE - MECANISME 4-BAR LINKAGE')
    subtitle(dwg, W / 2, 42, 'Quantites pour un mecanisme complet (haut + bas)')

    items = [
        ('PM', 'Platine murale combinee (A+B)',
         '2', f'Tole S235 {TOLE}mm pliee + 1 soudure',
         f'Patron deplie: {MUR_WIDTH}x{MUR_COTE_DEPTH + MUR_PLAT_DEPTH + MUR_FOND_H}mm'),
        ('PP', 'Platine porte combinee (a+b)',
         '2', f'Tole S235 {TOLE}mm pliee + 1 soudure',
         f'Patron deplie: {PORTE_WIDTH}x{PORTE_COTE_DEPTH + PORTE_PLAT_DEPTH + PORTE_FOND_H}mm'),
        ('BR1', f'Bras 1 long (A->a)',
         '2', f'Tube rect {BRAS_TUBE[0]}x{BRAS_TUBE[1]}x{BRAS_TUBE[2]}',
         f'L entraxe = {round(L1)}mm'),
        ('BR2', f'Bras 2 court (B->b)',
         '2', f'Tube rect {BRAS_TUBE[0]}x{BRAS_TUBE[1]}x{BRAS_TUBE[2]}',
         f'L entraxe = {round(L2)}mm'),
        ('BL1', f'Boulon pivot D{AXE_D}mm',
         '8', f'Classe 8.8, L~{AXE_L}mm',
         f'D{AXE_D} + rondelles + ecrou Nylstop'),
        ('RO', 'Rondelle plate large',
         '16', f'Acier zingue, D{AXE_D}',
         'Entre tole et tube, entre tube et ecrou'),
        ('CH', 'Cheville chimique M12',
         '12', 'Fischer FIS V ou equiv.',
         'Fixation fond platine murale (6/platine)'),
        ('BL2', 'Boulon traversant M8',
         '18', 'Classe 8.8 + Nylstop',
         'Fixation fond platine porte (9/platine)'),
        ('BT', 'Butee reglable',
         '2', 'Boulon M12x40 + contre-ecrou',
         '+ tampon EPDM 5mm'),
    ]

    # En-tete
    y = 65
    cols = [30, 80, 380, 420, 560, 750]
    headers = ['Ref', 'Description', 'Qte', 'Materiel', 'Dimensions']
    for c, h in zip(cols, headers):
        text(dwg, c, y, h, font_size='9px', font_weight='bold', text_anchor='start')
    y += 5
    line(dwg, 20, y, W - 20, y, stroke='black', stroke_width=1)

    for ref, desc, qty, mat, dims in items:
        y += 20
        for c, val in zip(cols, [ref, desc, qty, mat, dims]):
            text(dwg, c, y, val, font_size='8px', text_anchor='start')

    y += 10
    line(dwg, 20, y, W - 20, y, stroke='black', stroke_width=0.5)

    # Resume
    y += 25
    text(dwg, W / 2, y,
         'Design simplifie: 4 types de pieces seulement (platine murale, platine porte, bras long, bras court)',
         font_size='9px', fill='#555')
    text(dwg, W / 2, y + 15,
         'Traitement surface: galvanisation a chaud ou peinture epoxy 2 composants',
         font_size='9px', fill='#555')

    dwg.save()
    print(f"  {dwg.filename}")


# =============================================================================
if __name__ == '__main__':
    print("Generation des plans charnieres SVG...")
    plan_platine_murale()
    plan_platine_porte()
    plan_bras()
    plan_nomenclature()
    print(f"\nOuvrir dans le navigateur:")
    for f in ['platine_murale.svg', 'platine_porte.svg', 'bras.svg', 'nomenclature.svg']:
        print(f"  file://{os.path.join(outdir, f)}")
