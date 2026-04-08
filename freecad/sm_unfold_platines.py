"""
Script a executer dans la console Python de FreeCAD (avec GUI).
Cree les platines avec le Sheet Metal workbench et genere les patrons deplies.

Usage dans la console FreeCAD:
  exec(open('/home/sigo/Téléchargements/porte-buanderie/freecad/sm_unfold_platines.py').read())
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

DEPTH_A = Ay - RWD; DEPTH_B = By - RWD
DEPTH_a = ay_d - DT; DEPTH_b = by_d - DT


def find_edge(shape, min_len, **criteria):
    """Trouve un edge par criteres sur les coordonnees moyennes."""
    for i, edge in enumerate(shape.Edges):
        v1, v2 = edge.Vertexes[0].Point, edge.Vertexes[1].Point
        if edge.Length < min_len:
            continue
        ok = True
        for key, val in criteria.items():
            coord, bound = key.split('_')  # ex: 'z_near' -> coord='z', bound='near'
            mid = (getattr(v1, coord) + getattr(v2, coord)) / 2
            if bound == 'near' and abs(mid - val) > 2:
                ok = False
            elif bound == 'gt' and mid < val:
                ok = False
            elif bound == 'lt' and mid > val:
                ok = False
        if ok:
            return f'Edge{i+1}'
    return None


def create_sm_platine(doc, name, depth_dessus, depth_dessous,
                      dx_dessus, dx_dessous, cote_side='right'):
    """
    Cree une platine SM avec la bonne geometrie en L:
    - Fond (base) -> pli 1 (horizontal, le long de X) -> Plat
    - Plat -> pli 2 (vertical, le long d'un bord X du plat) -> Cote

    Perce les trous AVANT le depliage pour qu'ils apparaissent dans le patron.
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

    # --- Body + Sketch fond (ligne horizontale = largeur) ---
    body = doc.addObject('PartDesign::Body', name)
    sk = body.newObject('Sketcher::SketchObject', f'Sk_{name}')
    sk.AttachmentSupport = [(body.Origin.OriginFeatures[3], '')]
    sk.MapMode = 'FlatFace'
    sk.addGeometry(Part.LineSegment(
        App.Vector(x_min, 0, 0), App.Vector(x_max, 0, 0)), False)
    doc.recompute()

    # --- Base SM (= fond, extrude en Z de 0 a FOND_H) ---
    base = body.newObject('PartDesign::FeaturePython', f'Fond_{name}')
    SheetMetalBaseCmd.SMBaseBend(base, sk)
    base.Thickness = TOLE
    base.Length = FOND_H
    base.Radius = BEND_R
    base.BendSide = 'Outside'
    SheetMetalTools.SMViewProvider(base.ViewObject)
    doc.recompute()
    print(f"  Fond: {base.Shape.BoundBox}")

    # --- Pli 1: PLAT (depuis le bord sup du fond, z=FOND_H, y=0) ---
    edge_top = find_edge(base.Shape, w - 5, z_near=FOND_H, y_near=0)
    if not edge_top:
        print("  ERREUR: bord sup fond non trouve!")
        return None, None
    print(f"  Bord sup fond: {edge_top}")

    plat = body.newObject('PartDesign::FeaturePython', f'Plat_{name}')
    SheetMetalCmd.SMBendWall(plat, base, [edge_top])
    plat.radius = BEND_R
    plat.length = plat_depth
    plat.angle = 90.0
    plat.BendType = 'Material Outside'
    plat.LengthSpec = 'Leg'
    SheetMetalTools.SMViewProvider(plat.ViewObject)
    doc.recompute()
    print(f"  Plat: {plat.Shape.BoundBox}")

    # --- Pli 2: COTE (depuis le bord LATERAL du plat, pas le bord lointain) ---
    # Le bord lateral est un bord long (plat_depth) a x=x_min ou x=x_max,
    # dans la zone du plat (y > 0)
    if cote_side == 'right':
        # Bord a x_max, dans le plat (y > plat_depth/2), z pres de FOND_H+TOLE
        edge_side = find_edge(plat.Shape, plat_depth * 0.8,
                              x_near=x_max, y_gt=plat_depth * 0.3)
    else:
        edge_side = find_edge(plat.Shape, plat_depth * 0.8,
                              x_near=x_min, y_gt=plat_depth * 0.3)

    if not edge_side:
        # Fallback: chercher plus large
        print("  WARN: bord lateral non trouve, recherche elargie...")
        target_x = x_max if cote_side == 'right' else x_min
        for i, edge in enumerate(plat.Shape.Edges):
            v1, v2 = edge.Vertexes[0].Point, edge.Vertexes[1].Point
            mid_x = (v1.x + v2.x) / 2
            mid_y = (v1.y + v2.y) / 2
            if edge.Length > plat_depth * 0.5 and abs(mid_x - target_x) < 5:
                edge_side = f'Edge{i+1}'
                print(f"    Trouve: Edge{i+1} x={mid_x:.0f} y={mid_y:.0f} L={edge.Length:.0f}")
                break

    if not edge_side:
        print("  ERREUR: bord lateral plat non trouve!")
        # Lister les edges pour debug
        for i, edge in enumerate(plat.Shape.Edges):
            v1, v2 = edge.Vertexes[0].Point, edge.Vertexes[1].Point
            if edge.Length > 50:
                print(f"    Edge{i+1}: ({v1.x:.0f},{v1.y:.0f},{v1.z:.0f})->({v2.x:.0f},{v2.y:.0f},{v2.z:.0f}) L={edge.Length:.0f}")
        return body, None

    print(f"  Bord lateral plat: {edge_side}")

    cote_obj = body.newObject('PartDesign::FeaturePython', f'Cote_{name}')
    SheetMetalCmd.SMBendWall(cote_obj, plat, [edge_side])
    cote_obj.radius = BEND_R
    cote_obj.length = cote_h
    cote_obj.angle = 90.0
    cote_obj.BendType = 'Material Outside'
    cote_obj.LengthSpec = 'Leg'
    SheetMetalTools.SMViewProvider(cote_obj.ViewObject)
    doc.recompute()
    print(f"  Cote: {cote_obj.Shape.BoundBox}")

    # --- Trous pivot dans le plat (AVANT depliage) ---
    py_dessus = TOLE + max(depth_dessus, 20)
    py_dessous = TOLE + max(depth_dessous, 20)
    z_plat = FOND_H + TOLE/2 + BEND_R

    last_feat = cote_obj
    for label, px, py in [('PivA', dx_dessus, py_dessus),
                           ('PivB', dx_dessous, py_dessous)]:
        hole = Part.makeCylinder(AXE_HOLE/2, TOLE + 20,
            App.Vector(px, py, z_plat - 10), App.Vector(0, 0, 1))
        cut_feat = body.newObject('Part::Feature', f'{label}_{name}')
        cut_feat.Shape = last_feat.Shape.cut(hole)
        last_feat = cut_feat

    # Trous fixation fond
    for dx in [x_min + 25, 0, x_max - 25]:
        for dz in [FOND_H * 0.25, FOND_H * 0.75]:
            fix = Part.makeCylinder(6, TOLE + 10,
                App.Vector(dx, -5, dz), App.Vector(0, 1, 0))
            cut_feat = body.newObject('Part::Feature', f'Fix_{name}_{len(body.Group)}')
            cut_feat.Shape = last_feat.Shape.cut(fix)
            last_feat = cut_feat

    print(f"  Trous perces ({2 + 6} trous)")

    # --- Depliage (sur la piece SM, pas sur les cuts) ---
    print("  Depliage...")
    try:
        bac = BendAllowanceCalculator.from_single_value(0.44, 'ansi')
        ref_face, unfolded_shape, bend_lines, normal, bend_info = getUnfold(
            bac, cote_obj, 'Face1')

        # Appliquer les memes trous au patron deplie
        # Les trous dans le plat: dans le patron, le plat est deplie
        # On ne peut pas simplement couper les memes coordonnees car le depliage
        # transforme la geometrie. On montre le patron SM brut.

        unfold_obj = doc.addObject('Part::Feature', f'Deplie_{name}')
        unfold_obj.Shape = unfolded_shape
        unfold_obj.Placement = App.Placement(App.Vector(w + 100, 0, 0), App.Rotation())

        if bend_lines and bend_lines.Edges:
            bl = doc.addObject('Part::Feature', f'Plis_{name}')
            bl.Shape = bend_lines
            bl.Placement = unfold_obj.Placement
            if hasattr(bl, 'ViewObject'):
                bl.ViewObject.LineColor = (1.0, 0.0, 0.0)
                bl.ViewObject.LineWidth = 2.0

        print(f"  Deplie: {unfold_obj.Shape.BoundBox}")
        print(f"  {len(bend_info)} plis: {[f'{b.angle:.0f}deg R{b.radius:.0f}' for b in bend_info]}")

        return body, unfold_obj

    except Exception as e:
        print(f"  Depliage ECHOUE: {e}")
        import traceback; traceback.print_exc()
        return body, None


# =============================================================================
# EXECUTION
# =============================================================================
print("=" * 60)
print("Sheet Metal Unfold - Platines")
print("=" * 60)

doc = App.newDocument('SM_Platines')

# --- Platine murale ---
MUR_CX = (Ax + Bx) / 2
body_mur, deplie_mur = create_sm_platine(
    doc, 'PlatineMurale',
    DEPTH_A, DEPTH_B,
    Ax - MUR_CX, Bx - MUR_CX,
    cote_side='right')

# --- Platine porte (decalee en Y) ---
PORTE_CX = (ax_d + bx_d) / 2
body_porte, deplie_porte = create_sm_platine(
    doc, 'PlatinePorte',
    DEPTH_a, DEPTH_b,
    ax_d - PORTE_CX, bx_d - PORTE_CX,
    cote_side='left')

if body_porte:
    body_porte.Placement = App.Placement(App.Vector(0, -500, 0), App.Rotation())
if deplie_porte:
    deplie_porte.Placement = App.Placement(
        App.Vector(deplie_porte.Placement.Base.x, -500, 0), App.Rotation())
    plis = doc.getObject('Plis_PlatinePorte')
    if plis:
        plis.Placement = deplie_porte.Placement

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
print("Vue 3D:")
print("  Gauche: pieces pliees SM (avec trous)")
print("  Droite: patrons deplies SM")
print("  Rouge: lignes de pliage")
print()
print("Si le pli 2 (cote) n'est pas lateral, verifier")
print("l'edge detecte dans le log ci-dessus.")
