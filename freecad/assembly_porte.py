#!/usr/bin/env python3
"""
=============================================================================
ASSEMBLY FreeCAD : Mecanisme 4-bar linkage porte buanderie
Version 3 : platines pliees (0 soudure complexe) + tubes simples perces
=============================================================================

Design des platines (murales et porte):
  Tole pliee avec 2 plis a 90 deg, formant 3 cotes:
    - FOND: plaque contre le mur/porte, percee pour vis/chevilles
    - PLAT: perpendiculaire, tient le pivot (trou pour boulon-axe)
    - COTE: rabat parallele au fond, rigidifie le plat
  1 seule soudure: cote <-> fond (ferme le cadre)

Design des bras:
  Tubes rectangulaires simples, perces aux 2 extremites.
  Le boulon-pivot passe directement dans le tube.

Les bras 1 et 2 sont decales en Z pour eviter collision.
=============================================================================
"""

import sys, os, math
sys.path.insert(0, '/usr/lib/freecad/Mod/Assembly')
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

L1 = math.sqrt((Ax-ax_d)**2+(Ay-ay_d)**2)   # ~675mm
L2 = math.sqrt((Bx-bx_d)**2+(By-by_d)**2)   # ~446mm
Lc = math.sqrt((bx_d-ax_d)**2+(by_d-ay_d)**2)
ang_l = math.atan2(by_d-ay_d, bx_d-ax_d)
t1_0 = math.atan2(ay_d-Ay, ax_d-Ax)

# Profondeurs des pivots depuis les surfaces
DEPTH_A = Ay - RWD    # ~3mm  (A quasi a fleur du mur)
DEPTH_B = By - RWD    # ~107mm (B loin dans la buanderie)
DEPTH_a = ay_d - DT   # ~95mm
DEPTH_b = by_d - DT   # ~189mm

# Quincaillerie
TOLE = 5            # epaisseur tole platines
AXE_D = 16          # diametre boulon-pivot
AXE_HOLE = 18       # trou avec jeu
TUBE_W = 40         # largeur tube bras
TUBE_H = 25         # hauteur tube bras
TUBE_T = 3          # epaisseur paroi tube
PLATINE_W = 120     # largeur platines (direction X)
FOND_H = 150        # hauteur du fond (direction Z, pour vis)

# Positionnement Z:
# Toutes les platines au meme Z. Bras a (1) par-dessus le plat, bras b (2) par-dessous.
# Le pivot est entierement dans le plat. Le boulon traverse le plat et le tube.
Z_MID = DOOR_H / 2           # hauteur commune des plats de platine
Z_BRAS1 = Z_MID + TOLE/2 + TUBE_H/2    # bras a: dessus du plat + demi-tube
Z_BRAS2 = Z_MID - TOLE/2 - TUBE_H/2    # bras b: dessous du plat - demi-tube
ARM_Z_SEP = Z_BRAS1 - Z_BRAS2           # = TOLE + TUBE_H = 30mm

PIVOT_MARGIN = 15   # marge de matiere autour du trou pivot dans le plat

print(f"Pivots - profondeurs: A={DEPTH_A:.0f}mm B={DEPTH_B:.0f}mm a={DEPTH_a:.0f}mm b={DEPTH_b:.0f}mm")
print(f"Bras: L1={L1:.0f}mm L2={L2:.0f}mm")
print(f"Plats @ Z={Z_MID:.0f} | Bras1(dessus)@{Z_BRAS1:.0f} | Bras2(dessous)@{Z_BRAS2:.0f} | sep={ARM_Z_SEP:.0f}mm")


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
# GEOMETRIE: platine pliee (3 cotes)
# =============================================================================

def make_platine_combinee(depth_dessus, depth_dessous, dx_dessus, dx_dessous):
    """
    Platine combinee: 1 seule piece pour 2 pivots (A+B ou a+b).
    Tole pliee: fond + plat (avec 2 trous) + cote. 2 plis, 1 soudure.

    Le pivot 'dessus' a son boulon par-dessus (bras 1 au-dessus du plat).
    Le pivot 'dessous' a son boulon par-dessous (bras 2 en-dessous).

    Vue de dessus (plan XY) - le plat s'etend en +Y:

        fond (y=0, contre mur/porte)
        +--------------------------+
        |   vis    vis    vis  vis |
        +--------------------------+  <- pli 1
        |                          |
        |     [A] dessus           |  <- trou pivot A a y=depth_dessus
        |                          |
        |                          |
        |            [B] dessous   |  <- trou pivot B a y=depth_dessous
        |                          |
        +--------------------------+
        ^                          ^
        cote (pli 2 + soudure)     bord libre

    Parametres:
      depth_dessus/dessous: profondeur Y du pivot depuis la surface
      dx_dessus/dessous: position X du pivot (relatif au centre de la platine)

    Retourne le shape. Centre X=0, fond a y=0.
    """
    t = TOLE
    z_plat = Z_MID

    # Largeur: couvre les 2 pivots + marge
    margin = 40
    x_min = min(dx_dessus, dx_dessous) - margin
    x_max = max(dx_dessus, dx_dessous) + margin
    w = x_max - x_min
    x_offset = x_min  # decalage du bord gauche

    # Profondeur du plat: jusqu'au pivot le plus profond + marge
    max_depth = max(depth_dessus, depth_dessous)
    plat_depth = max_depth + PIVOT_MARGIN + AXE_HOLE/2

    fond_h = FOND_H
    z_fond_bottom = z_plat - fond_h / 2
    h_cote = z_plat - t/2 - z_fond_bottom

    shapes = []

    # FOND: plaque verticale XZ, a y=0
    fond = Part.makeBox(w, t, fond_h, App.Vector(x_offset, 0, z_fond_bottom))
    shapes.append(fond)

    # PLAT: plaque horizontale XY
    plat = Part.makeBox(w, plat_depth, t, App.Vector(x_offset, t, z_plat - t/2))
    shapes.append(plat)

    # COTE: plaque verticale YZ, sur le bord gauche (x = x_offset)
    if h_cote > 10:
        cote = Part.makeBox(t, plat_depth, h_cote,
                             App.Vector(x_offset, t, z_plat - t/2 - h_cote))
        shapes.append(cote)

    # BOULONS-PIVOTS integres
    axe_l = TOLE + TUBE_H + 15
    # Pivot dessus (boulon vers le haut)
    py_dessus = t + max(depth_dessus, 20)
    shapes.append(Part.makeCylinder(AXE_D/2, axe_l,
        App.Vector(dx_dessus, py_dessus, z_plat - t/2),
        App.Vector(0, 0, 1)))
    # Pivot dessous (boulon vers le bas)
    py_dessous = t + max(depth_dessous, 20)
    shapes.append(Part.makeCylinder(AXE_D/2, axe_l,
        App.Vector(dx_dessous, py_dessous, z_plat + t/2 - axe_l),
        App.Vector(0, 0, 1)))

    result = shapes[0]
    for s in shapes[1:]:
        result = result.fuse(s)

    # Trous fixation dans le fond (6 trous, grille 3x2)
    for dx in [x_offset + 25, (x_offset + x_max)/2, x_max - 25]:
        for dz in [-40, 40]:
            fix = Part.makeCylinder(6, t + 10,
                                     App.Vector(dx, -5, z_plat + dz),
                                     App.Vector(0, 1, 0))
            result = result.cut(fix)

    return result


def make_arm_tube(length):
    """
    Bras = tube rectangulaire simple, perce aux 2 bouts.
    Axe du tube le long de X. Centre en Y et Z a (0,0).
    Pivot gauche a x=0, pivot droit a x=length.
    """
    w, h, t = TUBE_W, TUBE_H, TUBE_T

    outer = Part.makeBox(length, w, h, App.Vector(0, -w/2, -h/2))
    inner = Part.makeBox(length, w-2*t, h-2*t, App.Vector(0, -w/2+t, -h/2+t))
    tube = outer.cut(inner)

    # Trous pivot (axe Z) a chaque extremite
    for x in [0, length]:
        hole = Part.makeCylinder(AXE_HOLE/2, h + 20,
                                  App.Vector(x, 0, -h/2 - 10),
                                  App.Vector(0, 0, 1))
        tube = tube.cut(hole)

    return tube


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
    cadre_g.Shape = Part.makeBox(CADRE_T, DT, DOOR_H, App.Vector(0, 0, 0))
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

# --- Platine murale combinee (A+B sur le mur droit) ---
print("  Platine murale combinee (A+B)...")
MUR_CENTER_X = (Ax + Bx) / 2
platine_mur = asm.newObject('Part::Feature', 'Platine_Murale')
platine_mur.Shape = make_platine_combinee(
    DEPTH_A, DEPTH_B,
    dx_dessus=Ax - MUR_CENTER_X,      # x local du pivot A
    dx_dessous=Bx - MUR_CENTER_X,     # x local du pivot B
)
platine_mur.Placement = App.Placement(App.Vector(MUR_CENTER_X, RWD, 0), App.Rotation())

# --- Platine porte combinee (a+b, en coords porte) ---
print("  Platine porte combinee (a+b)...")
PORTE_CENTER_X = (ax_d + bx_d) / 2
platine_porte = asm.newObject('Part::Feature', 'Platine_Porte')
platine_porte.Shape = make_platine_combinee(
    DEPTH_a, DEPTH_b,
    dx_dessus=ax_d - PORTE_CENTER_X,  # x local du pivot a
    dx_dessous=bx_d - PORTE_CENTER_X, # x local du pivot b
)
platine_porte.Placement = App.Placement(App.Vector(PORTE_CENTER_X, DT, 0), App.Rotation())

# --- Bras (tubes simples perces) ---
print("  Bras...")

bras1 = asm.newObject('Part::Feature', 'Bras1')
bras1.Shape = make_arm_tube(L1)
arm1_angle = math.atan2(ay_d-Ay, ax_d-Ax)
bras1.Placement = App.Placement(
    App.Vector(Ax, Ay, Z_BRAS1),
    App.Rotation(App.Vector(0,0,1), math.degrees(arm1_angle)))

bras2 = asm.newObject('Part::Feature', 'Bras2')
bras2.Shape = make_arm_tube(L2)
arm2_angle = math.atan2(by_d-By, bx_d-Bx)
bras2.Placement = App.Placement(
    App.Vector(Bx, By, Z_BRAS2),
    App.Rotation(App.Vector(0,0,1), math.degrees(arm2_angle)))

# Les boulons-pivots sont integres dans les platines (pas d'objets axes separes).


# =============================================================================
# JOINTS + GROUND
# =============================================================================
print("  Joints...")
try:
    import JointObject
    jg = asm.newObject('Assembly::JointGroup', 'Joints')

    # Ground: murs + platine murale (fixe)
    for obj in [mur_g, mur_d, platine_mur]:
        gj = jg.newObject('App::FeaturePython', f'Gnd_{obj.Name}')
        JointObject.GroundedJoint(gj, obj)
    if CADRE_T > 0:
        gj = jg.newObject('App::FeaturePython', 'Gnd_CG')
        JointObject.GroundedJoint(gj, cadre_g)
    if CADRE_H > 0:
        gj = jg.newObject('App::FeaturePython', 'Gnd_CD')
        JointObject.GroundedJoint(gj, cadre_d)

    def mk_rev(name, o1, o2, p1, p2):
        j = jg.newObject('App::FeaturePython', name)
        JointObject.Joint(j, 1)
        j.Reference1 = [o1, ['','']]; j.Reference2 = [o2, ['','']]
        j.Detach1 = True; j.Detach2 = True
        j.Placement1 = App.Placement(App.Vector(*p1), App.Rotation())
        j.Placement2 = App.Placement(App.Vector(*p2), App.Rotation())
        return j

    # Revolutes: platine_mur <-> bras <-> porte
    mk_rev('Rev_A', platine_mur, bras1, (Ax,Ay,Z_BRAS1), (0,0,0))
    mk_rev('Rev_a', bras1, porte, (L1,0,0), (ax_d,ay_d,Z_BRAS1))
    mk_rev('Rev_b', porte, bras2, (bx_d,by_d,Z_BRAS2), (L2,0,0))
    mk_rev('Rev_B', bras2, platine_mur, (0,0,0), (Bx,By,Z_BRAS2))
    print("  4 revolutes OK")
    try:
        r = asm.solve()
        print(f"  Solver: {'OK' if r==0 else 'FAIL'}")
    except Exception as e:
        print(f"  Solver: {e}")
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

    # Porte + platines porte + axes porte
    porte.Placement = dp

    # Platine porte combinee: offset local au centre entre a et b
    platine_porte.Placement = dp * App.Placement(
        App.Vector(PORTE_CENTER_X, DT, 0), App.Rotation())

    # (axes integres dans les platines, pas d'objets separes)

    # Bras
    bras1.Placement = App.Placement(
        App.Vector(Ax, Ay, Z_BRAS1),
        App.Rotation(App.Vector(0,0,1), math.degrees(math.atan2(aay-Ay, aax-Ax))))
    bras2.Placement = App.Placement(
        App.Vector(Bx, By, Z_BRAS2),
        App.Rotation(App.Vector(0,0,1), math.degrees(math.atan2(aby-By, abx-Bx))))

    if HAS_GUI:
        Gui.updateGui()


def animate(fps=25, duration=4.0):
    if not HAS_GUI:
        print("Pas de GUI. Utiliser goto(pct)."); return
    from PySide import QtCore
    n = int(fps*duration)
    st = {'f':0, 'd':1}
    def tick():
        goto(st['f']*100.0/n)
        st['f'] += st['d']
        if st['f']>n: st['d']=-1; st['f']=n-1
        elif st['f']<0: st['d']=1; st['f']=1
    timer = QtCore.QTimer()
    timer.timeout.connect(tick)
    global _anim_timer; _anim_timer = timer
    timer.start(int(1000/fps))
    print(f"Animation {fps}fps | stop() pour arreter")

def stop():
    global _anim_timer
    try: _anim_timer.stop(); print("OK")
    except: pass


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
sc(platine_mur, .6,.6,.65)
sc(platine_porte, .7,.55,.35)
sc(bras1, .78,.16,.16); sc(bras2, .08,.4,.75)
# Axes integres dans les platines

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
print(f"  Platine murale (A+B): pivots a {DEPTH_A:.0f}mm et {DEPTH_B:.0f}mm du mur")
print(f"  Platine porte  (a+b): pivots a {DEPTH_a:.0f}mm et {DEPTH_b:.0f}mm de la porte")
print(f"  Bras: tube {TUBE_W}x{TUBE_H}x{TUBE_T} perce D{AXE_HOLE}")
print(f"  Plats @ Z={Z_MID:.0f} | Bras1 DESSUS @{Z_BRAS1:.0f} | Bras2 DESSOUS @{Z_BRAS2:.0f}")
print(f"  Separation bras: {ARM_Z_SEP:.0f}mm (tole {TOLE} + tube {TUBE_H})")
print(f"  goto(50) / animate() / stop()")
