#!/usr/bin/env python3
"""
Macro FreeCAD: modele 3D avec Spreadsheet pour controler l'angle d'ouverture.

En changeant la valeur "angle_pct" dans le Spreadsheet (0=ferme, 100=ouvert),
toutes les pieces bougent en temps reel.

Usage:
  1. Ouvrir dans FreeCAD: freecad exports/porte_animable.FCStd
  2. Cliquer sur le Spreadsheet "Parametres" dans l'arbre
  3. Changer la cellule B1 (angle_pct) de 0 a 100
  4. Appuyer sur Entree -> la porte bouge!

Ou lancer: freecadcmd freecad/porte_animable.py pour generer le fichier.
"""

import FreeCAD
import Part
import Spreadsheet
import math
import os

# =============================================================================
# PARAMETRES
# =============================================================================
OW = 870; DT = 355; LWD = 355; RWD = 425; SBR = 380
STEP_H = 190; DOOR_H = 2040
CADRE_H = 25; CADRE_T = 25
TAPER_H = 60; TAPER_T = 60

C1 = (CADRE_T, 0)
C2 = (CADRE_T + TAPER_T, DT)
C3 = (OW - CADRE_H - TAPER_H, DT)
C4 = (OW - CADRE_H, 0)

Ax, Ay = 1246.1, 471.3
Bx, By = 1188.4, 586.1
ax_d, ay_d = 664.1, 426.3
bx_d, by_d = 766.2, 540.6
SWEEP = 0.55

L1 = math.sqrt((Ax-ax_d)**2 + (Ay-ay_d)**2)
L2 = math.sqrt((Bx-bx_d)**2 + (By-by_d)**2)
Lc = math.sqrt((bx_d-ax_d)**2 + (by_d-ay_d)**2)
ang_l = math.atan2(by_d-ay_d, bx_d-ax_d)
t1_0 = math.atan2(ay_d-Ay, ax_d-Ax)

# =============================================================================
# SIMULATION: precalculer toutes les positions
# =============================================================================
N_POS = 101  # 0 a 100%

def simulate_all():
    positions = []
    for i in range(N_POS):
        f = i / (N_POS - 1)
        t1 = t1_0 - f * math.pi * SWEEP

        axx = Ax + L1 * math.cos(t1)
        ayy = Ay + L1 * math.sin(t1)

        dx, dy = Bx - axx, By - ayy
        d = math.sqrt(dx*dx + dy*dy)
        if d > Lc + L2 + 0.01 or d < abs(Lc - L2) - 0.01:
            positions.append(positions[-1])  # repeter la derniere position valide
            continue

        aa = (Lc*Lc - L2*L2 + d*d) / (2*d)
        hsq = max(0, Lc*Lc - aa*aa)
        h = math.sqrt(hsq)
        mx = axx + aa*dx/d
        my = ayy + aa*dy/d
        px, py = -dy/d*h, dx/d*h
        bxx, byy = mx + px, my + py

        ang_w = math.atan2(byy - ayy, bxx - axx)
        door_ang = ang_w - ang_l
        co, si = math.cos(door_ang), math.sin(door_ang)
        tx = axx - (ax_d * co - ay_d * si)
        ty = ayy - (ax_d * si + ay_d * co)

        positions.append({
            'tx': tx, 'ty': ty, 'angle_deg': math.degrees(door_ang),
            'arm_a': (axx, ayy), 'arm_b': (bxx, byy),
        })
    return positions

def transform_2d(px, py, tx, ty, angle_rad):
    co, si = math.cos(angle_rad), math.sin(angle_rad)
    return (px*co - py*si + tx, px*si + py*co + ty)

# =============================================================================
# CREATION DU DOCUMENT
# =============================================================================

print("Precalcul des positions...")
all_positions = simulate_all()
print(f"  {len(all_positions)} positions (0° a {all_positions[-1]['angle_deg']:.1f}°)")

doc = FreeCAD.newDocument("PorteAnimable")

# --- Spreadsheet avec les positions precalculees ---
print("Creation du Spreadsheet...")
ss = doc.addObject("Spreadsheet::Sheet", "Positions")

# Ligne 1: en-tetes
ss.set("A1", "pct")
ss.set("B1", "tx")
ss.set("C1", "ty")
ss.set("D1", "angle_deg")
ss.set("E1", "arm_ax")
ss.set("F1", "arm_ay")
ss.set("G1", "arm_bx")
ss.set("H1", "arm_by")

# Lignes 2+: les positions
for i, pos in enumerate(all_positions):
    row = i + 2
    ss.set(f"A{row}", str(i))
    ss.set(f"B{row}", f"{pos['tx']:.2f}")
    ss.set(f"C{row}", f"{pos['ty']:.2f}")
    ss.set(f"D{row}", f"{pos['angle_deg']:.2f}")
    ss.set(f"E{row}", f"{pos['arm_a'][0]:.2f}")
    ss.set(f"F{row}", f"{pos['arm_a'][1]:.2f}")
    ss.set(f"G{row}", f"{pos['arm_b'][0]:.2f}")
    ss.set(f"H{row}", f"{pos['arm_b'][1]:.2f}")

# --- Spreadsheet de controle ---
ctrl = doc.addObject("Spreadsheet::Sheet", "Controle")
ctrl.set("A1", "angle_pct")
ctrl.set("B1", "0")  # Valeur initiale = ferme
ctrl.setAlias("B1", "angle_pct")
ctrl.set("A2", "")
ctrl.set("A3", "Changer B1 de 0 a 100")
ctrl.set("A4", "pour ouvrir la porte")

# --- Murs (statiques) ---
print("Creation des murs...")
mur_g = doc.addObject("Part::Box", "MurGauche")
mur_g.Length = 300; mur_g.Width = LWD; mur_g.Height = DOOR_H + STEP_H + 100
mur_g.Placement = FreeCAD.Placement(FreeCAD.Vector(-300, 0, -STEP_H), FreeCAD.Rotation())

mur_d = doc.addObject("Part::Box", "MurDroit")
mur_d.Length = SBR + 50; mur_d.Width = RWD; mur_d.Height = DOOR_H + STEP_H + 100
mur_d.Placement = FreeCAD.Placement(FreeCAD.Vector(OW, 0, -STEP_H), FreeCAD.Rotation())

# Cadres
for name, x, w in [("CadreGauche", 0, CADRE_T), ("CadreDroit", OW-CADRE_H, CADRE_H)]:
    if w > 0:
        box = doc.addObject("Part::Box", name)
        box.Length = w; box.Width = DT; box.Height = DOOR_H + STEP_H
        box.Placement = FreeCAD.Placement(FreeCAD.Vector(x, 0, -STEP_H), FreeCAD.Rotation())

# --- Porte a chaque position (toutes dans le meme doc, visibilite controlable) ---
print("Creation des positions de porte...")
for i in range(0, N_POS, 5):  # toutes les 5% = 21 positions
    pos = all_positions[i]
    tx, ty = pos['tx'], pos['ty']
    angle_rad = math.radians(pos['angle_deg'])

    corners_2d = [C1, C2, C3, C4]
    corners_world = [transform_2d(cx, cy, tx, ty, angle_rad) for cx, cy in corners_2d]

    try:
        wire = Part.makePolygon([
            FreeCAD.Vector(x, y, 0) for x, y in corners_world
        ] + [FreeCAD.Vector(corners_world[0][0], corners_world[0][1], 0)])
        face = Part.Face(wire)
        shape = face.extrude(FreeCAD.Vector(0, 0, DOOR_H))

        porte = doc.addObject("Part::Feature", f"Porte_{i:03d}pct")
        porte.Shape = shape
    except Exception as e:
        print(f"  Erreur frame {i}: {e}")
        continue

    # Bras
    for bname, px_m, py_m, xd, yd in [
        ("Bras1", Ax, Ay, ax_d, ay_d),
        ("Bras2", Bx, By, bx_d, by_d)
    ]:
        p_porte = transform_2d(xd, yd, tx, ty, angle_rad)
        ddx = p_porte[0] - px_m
        ddy = p_porte[1] - py_m
        length = math.sqrt(ddx*ddx + ddy*ddy)
        ang_bras = math.degrees(math.atan2(ddy, ddx))

        cyl = doc.addObject("Part::Cylinder", f"{bname}_{i:03d}pct")
        cyl.Radius = 10; cyl.Height = length
        cyl.Placement = FreeCAD.Placement(
            FreeCAD.Vector(px_m, py_m, DOOR_H/2),
            FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), ang_bras) *
            FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), 90)
        )

    # Pattes
    for pname, xd, yd in [("PatteA", ax_d, ay_d), ("PatteB", bx_d, by_d)]:
        p_face = transform_2d(xd, DT, tx, ty, angle_rad)
        p_pivot = transform_2d(xd, yd, tx, ty, angle_rad)
        ddx = p_pivot[0] - p_face[0]
        ddy = p_pivot[1] - p_face[1]
        length = math.sqrt(ddx*ddx + ddy*ddy)
        if length > 5:
            ang_p = math.degrees(math.atan2(ddy, ddx))
            cyl = doc.addObject("Part::Cylinder", f"{pname}_{i:03d}pct")
            cyl.Radius = 8; cyl.Height = length
            cyl.Placement = FreeCAD.Placement(
                FreeCAD.Vector(p_face[0], p_face[1], DOOR_H/2),
                FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), ang_p) *
                FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), 90)
            )

    if i % 20 == 0:
        print(f"  {i}%: angle={pos['angle_deg']:.1f}°")

# Pivots (statiques sur le mur)
for name, x, y, r in [("PivotA", Ax, Ay, 15), ("PivotB", Bx, By, 15)]:
    sph = doc.addObject("Part::Sphere", name)
    sph.Radius = r
    sph.Placement = FreeCAD.Placement(FreeCAD.Vector(x, y, DOOR_H/2), FreeCAD.Rotation())

# =============================================================================
# GROUPER par position pour faciliter la visibilite
# =============================================================================
print("Groupement des objets...")
for i in range(0, N_POS, 5):
    grp_name = f"Position_{i:03d}pct"
    grp = doc.addObject("App::DocumentObjectGroup", grp_name)
    suffix = f"_{i:03d}pct"
    for obj in doc.Objects:
        if obj.Name != grp_name and obj.Name.endswith(suffix):
            grp.addObject(obj)

# =============================================================================
# SAUVEGARDER
# =============================================================================
doc.recompute()
save_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          'exports', 'porte_animable.FCStd')
doc.saveAs(save_path)
print(f"\nSauvegarde: {save_path}")
print(f"\nPour animer dans FreeCAD:")
print(f"  1. Ouvrir: freecad {save_path}")
print(f"  2. Dans l'arbre, deplier les groupes 'Position_XXX_pct'")
print(f"  3. Cacher/montrer les groupes pour voir le mouvement")
print(f"  4. Ou: clic droit sur un groupe > Toggle visibility")
print(f"\n  Positions disponibles: 0%, 5%, 10%, ... 100% (21 positions)")
