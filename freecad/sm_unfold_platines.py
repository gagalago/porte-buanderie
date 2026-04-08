"""
Script a executer dans la console Python de FreeCAD (avec GUI).
Cree les platines avec le Sheet Metal workbench et genere les patrons deplies.

Usage dans la console FreeCAD:
  exec(open('/home/sigo/Téléchargements/porte-buanderie/freecad/sm_unfold_platines.py').read())

Resultat: un document avec pour chaque platine (murale + porte):
  - La piece 3D pliee (SM)
  - Le patron deplie (SM Unfold)
"""

import sys, math, os
sys.path.insert(0, os.path.expanduser('~/.local/share/FreeCAD/v1-1/Mod/sheetmetal'))

import FreeCAD as App
import FreeCADGui as Gui
import Part, Sketcher
import SheetMetalBaseCmd, SheetMetalCmd, SheetMetalTools
from SheetMetalNewUnfolder import getUnfold, BendAllowanceCalculator

# =============================================================================
# PARAMETRES
# =============================================================================
TOLE = 5; BEND_R = 3; AXE_HOLE = 18; FOND_H = 150; PIVOT_MARGIN = 15

Ax, Ay = 1246.1, 471.3; Bx, By = 1188.4, 586.1
ax_d, ay_d = 664.1, 426.3; bx_d, by_d = 766.2, 540.6
RWD = 425; DT = 355

DEPTH_A = Ay - RWD   # 46mm
DEPTH_B = By - RWD   # 161mm
DEPTH_a = ay_d - DT  # 71mm
DEPTH_b = by_d - DT  # 186mm


# =============================================================================
# CREATION SM
# =============================================================================

def create_sm_platine(doc, name, depth_dessus, depth_dessous,
                      dx_dessus, dx_dessous, cote_side='right'):
    """
    Cree une platine via Sheet Metal workbench:
    Fond (base) -> pli 1 -> Plat -> pli 2 -> Cote
    Puis deplie (Unfold) et perce les trous.

    Retourne (body, unfold_obj).
    """
    margin = 40
    x_min = min(dx_dessus, dx_dessous) - margin
    x_max = max(dx_dessus, dx_dessous) + margin
    w = x_max - x_min
    max_depth = max(depth_dessus, depth_dessous)
    plat_depth = max_depth + PIVOT_MARGIN + AXE_HOLE / 2
    cote_h = min(FOND_H * 0.6, 100)

    print(f"\n=== {name} ===")
    print(f"  Largeur: {w:.0f}mm | Plat: {plat_depth:.0f}mm | Cote: {cote_h:.0f}mm")

    # --- Body + Sketch fond ---
    body = doc.addObject('PartDesign::Body', name)
    sk = body.newObject('Sketcher::SketchObject', f'Sk_{name}')
    sk.AttachmentSupport = [(body.Origin.OriginFeatures[3], '')]
    sk.MapMode = 'FlatFace'
    sk.addGeometry(Part.LineSegment(
        App.Vector(x_min, 0, 0), App.Vector(x_max, 0, 0)), False)
    doc.recompute()

    # --- Base SM (= fond) ---
    base = body.newObject('PartDesign::FeaturePython', f'Fond_{name}')
    SheetMetalBaseCmd.SMBaseBend(base, sk)
    base.Thickness = TOLE
    base.Length = FOND_H
    base.Radius = BEND_R
    base.BendSide = 'Outside'
    SheetMetalTools.SMViewProvider(base.ViewObject)
    doc.recompute()
    print(f"  Fond OK: {base.Shape.BoundBox}")

    # --- Trouver le bord superieur du fond ---
    edge_top = find_edge(base.Shape, z_target=FOND_H, y_target=0, min_len=w - 5)
    print(f"  Bord sup fond: {edge_top}")

    # --- Pli 1: PLAT ---
    plat = body.newObject('PartDesign::FeaturePython', f'Plat_{name}')
    SheetMetalCmd.SMBendWall(plat, base, [edge_top])
    plat.radius = BEND_R
    plat.length = plat_depth
    plat.angle = 90.0
    plat.BendType = 'Material Outside'
    plat.LengthSpec = 'Leg'
    SheetMetalTools.SMViewProvider(plat.ViewObject)
    doc.recompute()
    print(f"  Plat OK: {plat.Shape.BoundBox}")

    # --- Trouver le bord du plat (cote interieur, y max, pour le raidisseur) ---
    # On veut le bord a y_max, longueur ~w, z interieur (plus petit z)
    best_edge = None
    best_z = 1e9
    for i, edge in enumerate(plat.Shape.Edges):
        v1, v2 = edge.Vertexes[0].Point, edge.Vertexes[1].Point
        mid_y = (v1.y + v2.y) / 2
        mid_z = (v1.z + v2.z) / 2
        if mid_y > plat_depth * 0.9 and edge.Length > w - 5 and mid_z < best_z:
            best_z = mid_z
            best_edge = f'Edge{i+1}'
    edge_far = best_edge or 'Edge21'
    print(f"  Bord plat (loin): {edge_far}")

    # --- Pli 2: COTE (raidisseur) ---
    cote = body.newObject('PartDesign::FeaturePython', f'Cote_{name}')
    SheetMetalCmd.SMBendWall(cote, plat, [edge_far])
    cote.radius = BEND_R
    cote.length = cote_h
    cote.angle = 90.0
    cote.BendType = 'Material Outside'
    cote.LengthSpec = 'Leg'
    SheetMetalTools.SMViewProvider(cote.ViewObject)
    doc.recompute()
    print(f"  Cote OK: {cote.Shape.BoundBox}")

    # --- Depliage ---
    print("  Depliage...")
    bac = BendAllowanceCalculator.from_single_value(0.44, 'ansi')
    ref_face, unfolded_shape, bend_lines, normal, bend_info = getUnfold(
        bac, cote, 'Face1')

    unfold_obj = doc.addObject('Part::Feature', f'Deplie_{name}')
    unfold_obj.Shape = unfolded_shape
    # Decaler a cote pour voir
    unfold_obj.Placement = App.Placement(
        App.Vector(w + 50, 0, 0), App.Rotation())

    # Lignes de pliage
    if bend_lines and bend_lines.Edges:
        bl = doc.addObject('Part::Feature', f'Plis_{name}')
        bl.Shape = bend_lines
        bl.Placement = unfold_obj.Placement
        bl.ViewObject.LineColor = (1.0, 0.0, 0.0)
        bl.ViewObject.LineWidth = 2.0

    print(f"  Deplie OK: {unfold_obj.Shape.BoundBox}")
    print(f"  {len(bend_info)} plis: {[f'{b.angle:.0f}deg R{b.radius:.0f}' for b in bend_info]}")

    # --- Trous pivot (coupes dans le deplie ET le plie) ---
    # Positions des trous dans le plat (coords du body non-deplie)
    py_dessus = TOLE + max(depth_dessus, 20)
    py_dessous = TOLE + max(depth_dessous, 20)
    z_plat = FOND_H + TOLE/2 + BEND_R  # z du milieu du plat apres pliage

    for px, py in [(dx_dessus, py_dessus), (dx_dessous, py_dessous)]:
        # Trou dans la piece pliee
        hole_3d = Part.makeCylinder(AXE_HOLE/2, TOLE + 20,
            App.Vector(px, py, z_plat - 10), App.Vector(0, 0, 1))
        cote.Shape = cote.Shape.cut(hole_3d)

    # Trous fixation dans le fond
    for dx in [x_min + 25, 0, x_max - 25]:
        for dz in [FOND_H * 0.25, FOND_H * 0.75]:
            fix = Part.makeCylinder(6, TOLE + 10,
                App.Vector(dx, -5, dz), App.Vector(0, 1, 0))
            cote.Shape = cote.Shape.cut(fix)

    doc.recompute()
    Gui.updateGui()

    return body, unfold_obj


def find_edge(shape, z_target, y_target, min_len):
    """Trouve un edge par position z, y et longueur min."""
    for i, edge in enumerate(shape.Edges):
        v1, v2 = edge.Vertexes[0].Point, edge.Vertexes[1].Point
        mid_z = (v1.z + v2.z) / 2
        if abs(mid_z - z_target) < 1 and abs(v1.y - y_target) < 1 and edge.Length > min_len:
            return f'Edge{i+1}'
    return 'Edge4'  # fallback


# =============================================================================
# EXECUTION
# =============================================================================
print("=" * 60)
print("Sheet Metal Unfold - Platines")
print("=" * 60)

doc = App.newDocument('SM_Platines')

# Platine murale
MUR_CX = (Ax + Bx) / 2
body_mur, deplie_mur = create_sm_platine(
    doc, 'PlatineMurale',
    DEPTH_A, DEPTH_B,
    Ax - MUR_CX, Bx - MUR_CX,
    cote_side='right')

# Decaler la platine porte plus bas
body_porte_offset = App.Vector(0, -500, 0)

# Platine porte
PORTE_CX = (ax_d + bx_d) / 2
body_porte, deplie_porte = create_sm_platine(
    doc, 'PlatinePorte',
    DEPTH_a, DEPTH_b,
    ax_d - PORTE_CX, bx_d - PORTE_CX,
    cote_side='left')
body_porte.Placement = App.Placement(body_porte_offset, App.Rotation())
deplie_porte.Placement = App.Placement(
    body_porte_offset + deplie_porte.Placement.Base, App.Rotation())
plis_porte = doc.getObject('Plis_PlatinePorte')
if plis_porte:
    plis_porte.Placement = deplie_porte.Placement

doc.recompute()

# Sauvegarder
save_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          'exports', 'sm_platines_unfold.FCStd')
doc.saveAs(save_path)

Gui.activeDocument().activeView().viewIsometric()
Gui.SendMsgToActiveView("ViewFit")

print(f"\n{'='*60}")
print(f"Sauvegarde: {save_path}")
print(f"{'='*60}")
print()
print("Dans la vue 3D:")
print("  - A gauche: pieces pliees (SM)")
print("  - A droite: patrons deplies (SM Unfold)")
print("  - Lignes rouges: lignes de pliage")
print()
print("Comparer avec le TechDraw dans assembly_porte.FCStd:")
print("  Plan_Patron_Murale et Plan_Patron_Porte")
