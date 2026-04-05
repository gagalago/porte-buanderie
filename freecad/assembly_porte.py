#!/usr/bin/env python3
"""
=============================================================================
ASSEMBLY FreeCAD : Mecanisme 4-bar linkage porte buanderie
Version 5 : double mecanisme (haut+bas) + TechDraw
=============================================================================

2 mecanismes identiques (haut et bas de la porte), chacun avec:
- 1 platine murale combinee (A+B) pliee en 3 faces
- 1 platine porte combinee (a+b) pliee en 3 faces
- 2 bras (tubes 40x25x3 perces)
- Boulons-pivots integres

TechDraw: vues 2D cotees (face, dessus, detail platine)

Usage:
  freecadcmd freecad/assembly_porte.py
  freecad exports/assembly_porte.FCStd
  Console: goto(50) / animate() / stop()
=============================================================================
"""

import sys, os, math
sys.path.insert(0, '/usr/lib/freecad/Mod/Assembly')
SM_PATH = os.path.expanduser('~/.local/share/FreeCAD/v1-1/Mod/sheetmetal')
if os.path.isdir(SM_PATH):
    sys.path.insert(0, SM_PATH)

import FreeCAD as App
import Part

HAS_GUI = App.GuiUp
if HAS_GUI:
    import FreeCADGui as Gui

# =============================================================================
# PARAMETRES
# =============================================================================
OW = 870; DT = 355; LWD = 355; RWD = 425; SBR = 380
CADRE_H = 25; CADRE_T = 25; TAPER_H = 60; TAPER_T = 60
DOOR_H = 2040
C1 = (CADRE_T, 0); C2 = (CADRE_T+TAPER_T, DT)
C3 = (OW-CADRE_H-TAPER_H, DT); C4 = (OW-CADRE_H, 0)

Ax, Ay = 1246.1, 471.3;  Bx, By = 1188.4, 586.1
ax_d, ay_d = 664.1, 426.3; bx_d, by_d = 766.2, 540.6
SWEEP = 0.55

L1 = math.sqrt((Ax-ax_d)**2+(Ay-ay_d)**2)
L2 = math.sqrt((Bx-bx_d)**2+(By-by_d)**2)
Lc = math.sqrt((bx_d-ax_d)**2+(by_d-ay_d)**2)
ang_l = math.atan2(by_d-ay_d, bx_d-ax_d)
t1_0 = math.atan2(ay_d-Ay, ax_d-Ax)

DEPTH_A = Ay - RWD; DEPTH_B = By - RWD
DEPTH_a = ay_d - DT; DEPTH_b = by_d - DT

# Quincaillerie
TOLE = 5; AXE_D = 16; AXE_HOLE = 18
TUBE_W = 40; TUBE_H = 25; TUBE_T = 3
FOND_H = 150; PIVOT_MARGIN = 15

# Double mecanisme: haut et bas de la porte
Z_HAUT = DOOR_H - 200   # 1840mm (centre mecanisme haut)
Z_BAS = 200              # 200mm (centre mecanisme bas)

MUR_CENTER_X = (Ax + Bx) / 2
PORTE_CENTER_X = (ax_d + bx_d) / 2

print(f"Mecanisme: L1={L1:.0f}mm L2={L2:.0f}mm")
print(f"Double mecanisme: Z_HAUT={Z_HAUT} Z_BAS={Z_BAS}")

# =============================================================================
# CINEMATIQUE
# =============================================================================
N_POS = 101

def simulate_all():
    best = None; best_s = -1e6
    for br in [0,1]:
        for di in [1,-1]:
            t1=t1_0; axx=Ax+L1*math.cos(t1); ayy=Ay+L1*math.sin(t1)
            dx,dy=Bx-axx,By-ayy; d=math.sqrt(dx*dx+dy*dy)
            if d>Lc+L2+.01 or d<abs(Lc-L2)-.01: continue
            aa=(Lc**2-L2**2+d**2)/(2*d); h=math.sqrt(max(0,Lc**2-aa**2))
            mx=axx+aa*dx/d; my=ayy+aa*dy/d; px,py=-dy/d*h,dx/d*h
            bxx,byy=(mx+px,my+py) if br==0 else (mx-px,my-py)
            aw=math.atan2(byy-ayy,bxx-axx); da=aw-ang_l
            co,si=math.cos(da),math.sin(da)
            tx=axx-(ax_d*co-ay_d*si); ty=ayy-(ax_d*si+ay_d*co)
            am=da%(2*math.pi)
            if am>math.pi: am-=2*math.pi
            if abs(tx)>5 or abs(ty)>5 or (abs(am)>.1 and abs(am-2*math.pi)>.1 and abs(am+2*math.pi)>.1): continue
            pos=[]; ok=True
            for i in range(N_POS):
                f=i/(N_POS-1); t1=t1_0+di*f*math.pi*SWEEP
                axx=Ax+L1*math.cos(t1); ayy=Ay+L1*math.sin(t1)
                dx,dy=Bx-axx,By-ayy; d=math.sqrt(dx*dx+dy*dy)
                if d>Lc+L2+.01 or d<abs(Lc-L2)-.01 or d<1e-10: ok=False; break
                aa=(Lc**2-L2**2+d**2)/(2*d); h=math.sqrt(max(0,Lc**2-aa**2))
                mx=axx+aa*dx/d; my=ayy+aa*dy/d; px,py=-dy/d*h,dx/d*h
                bxx,byy=(mx+px,my+py) if br==0 else (mx-px,my-py)
                aw=math.atan2(byy-ayy,bxx-axx); da=aw-ang_l
                co,si=math.cos(da),math.sin(da)
                tx=axx-(ax_d*co-ay_d*si); ty=ayy-(ax_d*si+ay_d*co)
                pos.append({'tx':tx,'ty':ty,'angle_deg':math.degrees(da),
                            'arm_a':(axx,ayy),'arm_b':(bxx,byy)})
            if not ok: continue
            s=abs(pos[-1]['angle_deg'])
            if s>best_s: best_s=s; best=pos
    return best

print("Cinematique...")
ALL_POS = simulate_all()
if not ALL_POS: print("ERREUR"); sys.exit(1)
print(f"  {len(ALL_POS)} positions, rot max = {ALL_POS[-1]['angle_deg']:.1f} deg")

# =============================================================================
# GEOMETRIE
# =============================================================================

def make_platine_combinee(depth_dessus, depth_dessous, dx_dessus, dx_dessous,
                          z_mid, cote_side='right'):
    """Platine combinee pliable: fond + plat (au sommet) + cote (bord du plat)."""
    t = TOLE; margin = 40
    x_min = min(dx_dessus, dx_dessous) - margin
    x_max = max(dx_dessus, dx_dessous) + margin
    w = x_max - x_min
    max_depth = max(depth_dessus, depth_dessous)
    plat_depth = max_depth + PIVOT_MARGIN + AXE_HOLE/2
    z_top = z_mid; z_bottom = z_top - FOND_H
    cote_h = min(FOND_H * 0.6, 100)
    z_bras1 = z_mid + t/2 + TUBE_H/2
    z_bras2 = z_mid - t/2 - TUBE_H/2

    shapes = []
    # FOND
    shapes.append(Part.makeBox(w, t, FOND_H, App.Vector(x_min, 0, z_bottom)))
    # PLAT (au sommet du fond)
    shapes.append(Part.makeBox(w, plat_depth, t, App.Vector(x_min, t, z_top - t)))
    # COTE (bord oppose aux bras)
    cote_x = (x_max - t) if cote_side == 'right' else x_min
    shapes.append(Part.makeBox(t, plat_depth, cote_h,
                                App.Vector(cote_x, t, z_top - t - cote_h)))

    # BOULONS integres
    axe_l = TOLE + TUBE_H + 15
    py_dessus = t + max(depth_dessus, 20)
    py_dessous = t + max(depth_dessous, 20)
    shapes.append(Part.makeCylinder(AXE_D/2, axe_l,
        App.Vector(dx_dessus, py_dessus, z_top - t), App.Vector(0,0,1)))
    shapes.append(Part.makeCylinder(AXE_D/2, axe_l,
        App.Vector(dx_dessous, py_dessous, z_top - axe_l), App.Vector(0,0,1)))

    result = shapes[0]
    for s in shapes[1:]: result = result.fuse(s)

    # Trous pivot
    for px, py in [(dx_dessus, py_dessus), (dx_dessous, py_dessous)]:
        result = result.cut(Part.makeCylinder(AXE_HOLE/2, t+20,
            App.Vector(px, py, z_top-t-10), App.Vector(0,0,1)))
    # Trous fixation fond
    for dx in [x_min+25, 0, x_max-25]:
        for dz in [z_bottom+FOND_H*0.25, z_bottom+FOND_H*0.75]:
            result = result.cut(Part.makeCylinder(6, t+10,
                App.Vector(dx, -5, dz), App.Vector(0,1,0)))
    return result


def make_patron_plat(depth_dessus, depth_dessous, dx_dessus, dx_dessous,
                     cote_side='right'):
    """
    Patron a plat (mise a plat / depliage) de la platine combinee.
    Les 3 faces sont depliees dans le plan XY:

        Y=0                                                      Y=total
        +----FOND (150mm)----+--BA--+----PLAT (~185mm)----+--BA--+--COTE--+
        |                    |      |                     |      |        |
        |  (vis holes)       |      |  [A]   [B] pivots   |      |        |
        |                    |      |                     |      |        |
        +--------------------+------+---------------------+------+--------+

    BA = bend allowance (tolerance de pliage ~8mm pour R=3, t=5, K=0.44)
    Les lignes de pliage sont a Y=FOND_H et Y=FOND_H+BA+plat_depth.

    Retourne (shape, bend_line_y1, bend_line_y2) pour le marquage.
    """
    t = TOLE; margin = 40; BEND_R = 3; K_FACTOR = 0.44

    x_min = min(dx_dessus, dx_dessous) - margin
    x_max = max(dx_dessus, dx_dessous) + margin
    w = x_max - x_min

    max_depth = max(depth_dessus, depth_dessous)
    plat_depth = max_depth + PIVOT_MARGIN + AXE_HOLE/2
    cote_h = min(FOND_H * 0.6, 100)

    # Bend allowance pour pli 90 deg
    BA = (math.pi / 2) * (BEND_R + K_FACTOR * t)  # ~8.2mm

    # Positions Y des sections dans le patron
    fond_start = 0
    fond_end = FOND_H
    bend1_center = fond_end + BA / 2
    plat_start = fond_end + BA
    plat_end = plat_start + plat_depth
    bend2_center = plat_end + BA / 2
    cote_start = plat_end + BA
    cote_end = cote_start + cote_h

    # Shape: plaque plate complete
    shape = Part.makeBox(w, cote_end, t, App.Vector(x_min, 0, 0))

    # Trous pivot dans la section plat
    py_dessus = plat_start + t + max(depth_dessus, 20)
    py_dessous = plat_start + t + max(depth_dessous, 20)
    for px, py in [(dx_dessus, py_dessus), (dx_dessous, py_dessous)]:
        shape = shape.cut(Part.makeCylinder(AXE_HOLE/2, t+20,
            App.Vector(px, py, -10), App.Vector(0,0,1)))

    # Trous fixation dans la section fond
    for dx in [x_min+25, 0, x_max-25]:
        for dy in [FOND_H*0.25, FOND_H*0.75]:
            shape = shape.cut(Part.makeCylinder(6, t+10,
                App.Vector(dx, dy, -5), App.Vector(0,0,1)))

    # Lignes de pliage (fines rainures pour les marquer visuellement)
    for by in [bend1_center, bend2_center]:
        groove = Part.makeBox(w, 1, t*0.3, App.Vector(x_min, by-0.5, t*0.7))
        shape = shape.cut(groove)

    return shape, bend1_center, bend2_center


def make_arm_tube(length):
    """Tube rect 40x25x3 perce D18 aux extremites."""
    w,h,t = TUBE_W, TUBE_H, TUBE_T
    outer = Part.makeBox(length, w, h, App.Vector(0, -w/2, -h/2))
    inner = Part.makeBox(length, w-2*t, h-2*t, App.Vector(0, -w/2+t, -h/2+t))
    tube = outer.cut(inner)
    for x in [0, length]:
        tube = tube.cut(Part.makeCylinder(AXE_HOLE/2, h+20,
            App.Vector(x, 0, -h/2-10), App.Vector(0,0,1)))
    return tube


def create_mechanism(asm, suffix, z_mid):
    """Cree un jeu complet de mecanisme a une hauteur z_mid.
    Retourne un dict des objets mobiles pour l'animation."""
    z_bras1 = z_mid + TOLE/2 + TUBE_H/2
    z_bras2 = z_mid - TOLE/2 - TUBE_H/2

    # Platine murale
    pm = asm.newObject('Part::Feature', f'PlatMur{suffix}')
    pm.Shape = make_platine_combinee(
        DEPTH_A, DEPTH_B,
        Ax - MUR_CENTER_X, Bx - MUR_CENTER_X,
        z_mid, cote_side='right')
    pm.Placement = App.Placement(App.Vector(MUR_CENTER_X, RWD, 0), App.Rotation())

    # Platine porte
    pp = asm.newObject('Part::Feature', f'PlatPorte{suffix}')
    pp.Shape = make_platine_combinee(
        DEPTH_a, DEPTH_b,
        ax_d - PORTE_CENTER_X, bx_d - PORTE_CENTER_X,
        z_mid, cote_side='left')
    pp.Placement = App.Placement(App.Vector(PORTE_CENTER_X, DT, 0), App.Rotation())

    # Bras
    b1 = asm.newObject('Part::Feature', f'Bras1{suffix}')
    b1.Shape = make_arm_tube(L1)
    b1.Placement = App.Placement(App.Vector(Ax, Ay, z_bras1),
        App.Rotation(App.Vector(0,0,1), math.degrees(math.atan2(ay_d-Ay, ax_d-Ax))))

    b2 = asm.newObject('Part::Feature', f'Bras2{suffix}')
    b2.Shape = make_arm_tube(L2)
    b2.Placement = App.Placement(App.Vector(Bx, By, z_bras2),
        App.Rotation(App.Vector(0,0,1), math.degrees(math.atan2(by_d-By, bx_d-Bx))))

    return {'pm': pm, 'pp': pp, 'b1': b1, 'b2': b2,
            'z_bras1': z_bras1, 'z_bras2': z_bras2}


# =============================================================================
# CREATION DU DOCUMENT
# =============================================================================
print("\nCreation du document...")
doc = App.newDocument('PorteBuanderie')
asm = doc.addObject('Assembly::AssemblyObject', 'Assembly')
asm.Type = 'Assembly'

# --- Murs ---
print("  Murs...")
mur_g = asm.newObject('Part::Feature', 'MurGauche')
mur_g.Shape = Part.makeBox(300, LWD, DOOR_H+200, App.Vector(-300, 0, -100))
mur_d = asm.newObject('Part::Feature', 'MurDroit')
mur_d.Shape = Part.makeBox(SBR+50, RWD, DOOR_H+200, App.Vector(OW, 0, -100))

if CADRE_T > 0:
    cadre_g = asm.newObject('Part::Feature', 'CadreGauche')
    cadre_g.Shape = Part.makeBox(CADRE_T, DT, DOOR_H)
if CADRE_H > 0:
    cadre_d = asm.newObject('Part::Feature', 'CadreDroit')
    cadre_d.Shape = Part.makeBox(CADRE_H, DT, DOOR_H, App.Vector(OW-CADRE_H, 0, 0))

# --- Porte ---
print("  Porte...")
door_wire = Part.makePolygon([
    App.Vector(C1[0],C1[1],0), App.Vector(C4[0],C4[1],0),
    App.Vector(C3[0],C3[1],0), App.Vector(C2[0],C2[1],0),
    App.Vector(C1[0],C1[1],0)])
porte = asm.newObject('Part::Feature', 'Porte')
porte.Shape = Part.Face(door_wire).extrude(App.Vector(0, 0, DOOR_H))

# --- Double mecanisme ---
print("  Mecanisme HAUT...")
mech_h = create_mechanism(asm, '_H', Z_HAUT)
print("  Mecanisme BAS...")
mech_b = create_mechanism(asm, '_B', Z_BAS)
mechanisms = [mech_h, mech_b]

# --- Joints ---
print("  Joints...")
try:
    import JointObject
    jg = asm.newObject('Assembly::JointGroup', 'Joints')
    for obj in [mur_g, mur_d, mech_h['pm'], mech_b['pm']]:
        gj = jg.newObject('App::FeaturePython', f'Gnd_{obj.Name}')
        JointObject.GroundedJoint(gj, obj)
    if CADRE_T > 0:
        gj = jg.newObject('App::FeaturePython', 'Gnd_CG')
        JointObject.GroundedJoint(gj, cadre_g)
    if CADRE_H > 0:
        gj = jg.newObject('App::FeaturePython', 'Gnd_CD')
        JointObject.GroundedJoint(gj, cadre_d)
    print("  Joints OK")
except Exception as e:
    print(f"  Joints: {e}")


# =============================================================================
# ANIMATION
# =============================================================================

def goto(pct):
    idx = max(0, min(N_POS-1, int(round(pct*(N_POS-1)/100.0))))
    p = ALL_POS[idx]
    tx,ty,ad = p['tx'], p['ty'], p['angle_deg']
    aax,aay = p['arm_a']; abx,aby = p['arm_b']

    dp = App.Placement(App.Vector(tx,ty,0), App.Rotation(App.Vector(0,0,1), ad))
    porte.Placement = dp

    for m in mechanisms:
        # Platine porte
        m['pp'].Placement = dp * App.Placement(App.Vector(PORTE_CENTER_X, DT, 0), App.Rotation())
        # Bras
        m['b1'].Placement = App.Placement(App.Vector(Ax, Ay, m['z_bras1']),
            App.Rotation(App.Vector(0,0,1), math.degrees(math.atan2(aay-Ay, aax-Ax))))
        m['b2'].Placement = App.Placement(App.Vector(Bx, By, m['z_bras2']),
            App.Rotation(App.Vector(0,0,1), math.degrees(math.atan2(aby-By, abx-Bx))))

    if HAS_GUI: Gui.updateGui()


def animate(fps=25, duration=4.0):
    if not HAS_GUI: print("Pas de GUI."); return
    from PySide import QtCore
    n = int(fps*duration)
    st = {'f':0, 'd':1}
    def tick():
        goto(st['f']*100.0/n); st['f'] += st['d']
        if st['f']>n: st['d']=-1; st['f']=n-1
        elif st['f']<0: st['d']=1; st['f']=1
    timer = QtCore.QTimer(); timer.timeout.connect(tick)
    global _anim_timer; _anim_timer = timer
    timer.start(int(1000/fps)); print(f"Animation {fps}fps | stop()")

def stop():
    global _anim_timer
    try: _anim_timer.stop(); print("OK")
    except: pass


# =============================================================================
# TECHDRAW
# =============================================================================
print("  TechDraw...")
try:
    # Page principale: vues de l'assembly
    page = doc.addObject('TechDraw::DrawPage', 'Plan_Assembly')
    tpl = doc.addObject('TechDraw::DrawSVGTemplate', 'Template')
    tpl.Template = '/usr/share/freecad/Mod/TechDraw/Templates/ISO/A3_Landscape_blank.svg'
    page.Template = tpl

    # Vue de face (depuis la cuisine, direction -Y)
    vue_face = doc.addObject('TechDraw::DrawViewPart', 'Vue_Face')
    vue_face.Source = [porte, mech_h['pm'], mech_b['pm'],
                       mech_h['b1'], mech_h['b2'], mech_b['b1'], mech_b['b2'],
                       mech_h['pp'], mech_b['pp']]
    vue_face.Direction = App.Vector(0, -1, 0)
    vue_face.XDirection = App.Vector(1, 0, 0)
    vue_face.Scale = 0.08
    vue_face.X = 150; vue_face.Y = 150
    page.addView(vue_face)

    # Vue de dessus (direction -Z)
    vue_dessus = doc.addObject('TechDraw::DrawViewPart', 'Vue_Dessus')
    vue_dessus.Source = vue_face.Source
    vue_dessus.Direction = App.Vector(0, 0, -1)
    vue_dessus.XDirection = App.Vector(1, 0, 0)
    vue_dessus.Scale = 0.08
    vue_dessus.X = 150; vue_dessus.Y = 50
    page.addView(vue_dessus)

    # Page detail: platine murale seule
    page2 = doc.addObject('TechDraw::DrawPage', 'Plan_Platine')
    tpl2 = doc.addObject('TechDraw::DrawSVGTemplate', 'Template2')
    tpl2.Template = '/usr/share/freecad/Mod/TechDraw/Templates/ISO/A4_Portrait_blank.svg'
    page2.Template = tpl2

    # Vue isometrique de la platine murale
    vue_pm = doc.addObject('TechDraw::DrawViewPart', 'Vue_PlatMur')
    vue_pm.Source = [mech_h['pm']]
    vue_pm.Direction = App.Vector(1, -1, 1).normalize()
    vue_pm.Scale = 0.3
    vue_pm.X = 105; vue_pm.Y = 200
    page2.addView(vue_pm)

    # Vue de face de la platine murale
    vue_pm_face = doc.addObject('TechDraw::DrawViewPart', 'Vue_PlatMur_Face')
    vue_pm_face.Source = [mech_h['pm']]
    vue_pm_face.Direction = App.Vector(0, -1, 0)
    vue_pm_face.Scale = 0.5
    vue_pm_face.X = 105; vue_pm_face.Y = 80
    page2.addView(vue_pm_face)

    # === Page 3: MISE A PLAT (patrons deplies) ===
    page3 = doc.addObject('TechDraw::DrawPage', 'Plan_MiseAPlat')
    tpl3 = doc.addObject('TechDraw::DrawSVGTemplate', 'Template3')
    tpl3.Template = '/usr/share/freecad/Mod/TechDraw/Templates/ISO/A3_Landscape_blank.svg'
    page3.Template = tpl3

    # Patron plat: platine murale
    patron_mur = doc.addObject('Part::Feature', 'Patron_Murale')
    pm_shape, pm_b1, pm_b2 = make_patron_plat(
        DEPTH_A, DEPTH_B,
        Ax - MUR_CENTER_X, Bx - MUR_CENTER_X,
        cote_side='right')
    patron_mur.Shape = pm_shape
    patron_mur.Placement = App.Placement(App.Vector(-600, -400, 0), App.Rotation())

    vue_patron_mur = doc.addObject('TechDraw::DrawViewPart', 'Vue_Patron_Murale')
    vue_patron_mur.Source = [patron_mur]
    vue_patron_mur.Direction = App.Vector(0, 0, -1)  # vue de dessus
    vue_patron_mur.XDirection = App.Vector(1, 0, 0)
    vue_patron_mur.Scale = 0.6
    vue_patron_mur.X = 100; vue_patron_mur.Y = 190
    page3.addView(vue_patron_mur)

    # Patron plat: platine porte
    patron_porte = doc.addObject('Part::Feature', 'Patron_Porte')
    pp_shape, pp_b1, pp_b2 = make_patron_plat(
        DEPTH_a, DEPTH_b,
        ax_d - PORTE_CENTER_X, bx_d - PORTE_CENTER_X,
        cote_side='left')
    patron_porte.Shape = pp_shape
    patron_porte.Placement = App.Placement(App.Vector(-600, -800, 0), App.Rotation())

    vue_patron_porte = doc.addObject('TechDraw::DrawViewPart', 'Vue_Patron_Porte')
    vue_patron_porte.Source = [patron_porte]
    vue_patron_porte.Direction = App.Vector(0, 0, -1)
    vue_patron_porte.XDirection = App.Vector(1, 0, 0)
    vue_patron_porte.Scale = 0.5
    vue_patron_porte.X = 100; vue_patron_porte.Y = 70
    page3.addView(vue_patron_porte)

    print("  TechDraw: 3 pages (assembly + detail platine + mise a plat)")
except Exception as e:
    print(f"  TechDraw: {e}")


# =============================================================================
# COULEURS
# =============================================================================
print("  Couleurs...")
def sc(obj, r, g, b, tr=0):
    if HAS_GUI and hasattr(obj, 'ViewObject'):
        obj.ViewObject.ShapeColor = (r,g,b); obj.ViewObject.Transparency = tr

sc(mur_g, .75,.75,.75); sc(mur_d, .75,.75,.75)
if CADRE_T>0: sc(cadre_g, .55,.43,.39, 20)
if CADRE_H>0: sc(cadre_d, .55,.43,.39, 20)
sc(porte, .4,.73,.42, 30)
for m in mechanisms:
    sc(m['pm'], .6,.6,.65); sc(m['pp'], .7,.55,.35)
    sc(m['b1'], .78,.16,.16); sc(m['b2'], .08,.4,.75)

# Cacher les patrons dans la vue 3D (visibles uniquement dans TechDraw)
for name in ['Patron_Murale', 'Patron_Porte']:
    obj = doc.getObject(name)
    if obj and HAS_GUI:
        obj.ViewObject.Visibility = False

# =============================================================================
# SAVE
# =============================================================================
doc.recompute()
goto(0)

save_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'exports')
os.makedirs(save_dir, exist_ok=True)
save_path = os.path.join(save_dir, 'assembly_porte.FCStd')
doc.saveAs(save_path)

print(f"\n{'='*60}")
print(f"Sauvegarde: {save_path}")
print(f"{'='*60}")
print(f"  2 mecanismes: Z_HAUT={Z_HAUT}mm Z_BAS={Z_BAS}mm")
print(f"  Platine murale (A+B): pivots a {DEPTH_A:.0f}mm et {DEPTH_B:.0f}mm du mur")
print(f"  Platine porte  (a+b): pivots a {DEPTH_a:.0f}mm et {DEPTH_b:.0f}mm de la porte")
print(f"  Bras: tube {TUBE_W}x{TUBE_H}x{TUBE_T} perce D{AXE_HOLE}")
print(f"  TechDraw: 2 pages (Plan_Assembly + Plan_Platine)")
print(f"  goto(50) / animate() / stop()")
