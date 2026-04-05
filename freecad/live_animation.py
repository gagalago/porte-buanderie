#!/usr/bin/env python3
"""
Envoie le modele complet + animation live a FreeCAD via socket.

Etape 1: Cree le modele (murs, porte, bras, pivots)
Etape 2: Anime en boucle en mettant a jour les Placements
"""
import socket
import time
import math

HOST = 'localhost'
PORT = 9876

def send(code: str, retries=5):
    for attempt in range(retries):
        try:
            with socket.create_connection((HOST, PORT), timeout=5) as s:
                s.sendall(code.encode())
            time.sleep(0.1)
            return
        except (ConnectionRefusedError, ConnectionResetError, OSError) as e:
            if attempt < retries - 1:
                time.sleep(0.5)
            else:
                raise RuntimeError(f"Impossible de se connecter apres {retries} essais: {e}")

# =============================================================================
# ETAPE 1: Creer le modele statique dans FreeCAD
# =============================================================================
print("Creation du modele dans FreeCAD...")

send("""
import FreeCAD as App
import Part
import math

# Fermer les docs existants
for name in list(App.listDocuments().keys()):
    App.closeDocument(name)

doc = App.newDocument("PorteAnimation")
App.setActiveDocument("PorteAnimation")

# Parametres
OW=870; DT=355; LWD=355; RWD=425; SBR=380
STEP_H=190; DOOR_H=2040
CADRE_H=25; CADRE_T=25; TAPER_H=60; TAPER_T=60

# Coins porte
C1=(CADRE_T, 0); C2=(CADRE_T+TAPER_T, DT)
C3=(OW-CADRE_H-TAPER_H, DT); C4=(OW-CADRE_H, 0)

# Mecanisme
Ax,Ay=1237.7,427.9; Bx,By=1188.4,531.6
ax_d,ay_d=563.3,450.2; bx_d,by_d=742.7,543.8

# --- Mur gauche ---
mg = doc.addObject("Part::Box","MurGauche")
mg.Length=300; mg.Width=LWD; mg.Height=DOOR_H+STEP_H+100
mg.Placement=App.Placement(App.Vector(-300,0,-STEP_H),App.Rotation())
mg.ViewObject.ShapeColor=(0.75,0.75,0.75)
mg.ViewObject.Transparency=70

# --- Mur droit ---
md = doc.addObject("Part::Box","MurDroit")
md.Length=SBR+50; md.Width=RWD; md.Height=DOOR_H+STEP_H+100
md.Placement=App.Placement(App.Vector(OW,0,-STEP_H),App.Rotation())
md.ViewObject.ShapeColor=(0.75,0.75,0.75)
md.ViewObject.Transparency=70

# --- Cadres ---
for name,x,w in [("CadreG",0,CADRE_T),("CadreD",OW-CADRE_H,CADRE_H)]:
    b=doc.addObject("Part::Box",name)
    b.Length=w; b.Width=DT; b.Height=DOOR_H+STEP_H
    b.Placement=App.Placement(App.Vector(x,0,-STEP_H),App.Rotation())
    b.ViewObject.ShapeColor=(0.55,0.43,0.35)
    b.ViewObject.Transparency=40

# --- Sol cuisine ---
sc=doc.addObject("Part::Box","SolCuisine")
sc.Length=OW+600; sc.Width=200; sc.Height=STEP_H
sc.Placement=App.Placement(App.Vector(-300,-200,0),App.Rotation())
sc.ViewObject.ShapeColor=(1.0,0.9,0.75)
sc.ViewObject.Transparency=70

# --- Sol buanderie ---
sb=doc.addObject("Part::Box","SolBuanderie")
sb.Length=OW+600; sb.Width=1500; sb.Height=10
sb.Placement=App.Placement(App.Vector(-300,0,-10),App.Rotation())
sb.ViewObject.ShapeColor=(0.85,0.85,0.85)
sb.ViewObject.Transparency=80

# --- Pivots mur (spheres fixes) ---
for name,x,y,col in [("PivotA",Ax,Ay,(0.9,0.1,0.1)),("PivotB",Bx,By,(0.1,0.1,0.9))]:
    s=doc.addObject("Part::Sphere",name)
    s.Radius=15
    s.Placement=App.Placement(App.Vector(x,y,DOOR_H/2),App.Rotation())
    s.ViewObject.ShapeColor=col

# --- Porte (sera bougee par l'animation) ---
wire=Part.makePolygon([App.Vector(*c,0) for c in [C1,C2,C3,C4,C1]])
face=Part.Face(wire)
shape=face.extrude(App.Vector(0,0,DOOR_H))
porte=doc.addObject("Part::Feature","Porte")
porte.Shape=shape
porte.ViewObject.ShapeColor=(0.4,0.8,0.4)
porte.ViewObject.Transparency=20

# --- Bras (cylindres, seront mis a jour) ---
for name,col in [("Bras1",(0.8,0.2,0.2)),("Bras2",(0.2,0.2,0.8))]:
    c=doc.addObject("Part::Cylinder",name)
    c.Radius=10; c.Height=100
    c.ViewObject.ShapeColor=col

# --- Pattes (cylindres, seront mis a jour) ---
for name,col in [("PatteA",(0.9,0.3,0.3)),("PatteB",(0.3,0.3,0.9))]:
    c=doc.addObject("Part::Cylinder",name)
    c.Radius=8; c.Height=100
    c.ViewObject.ShapeColor=col

doc.recompute()
Gui.activeDocument().activeView().viewIsometric()
Gui.SendMsgToActiveView("ViewFit")
print("Modele cree!")
""")

print("  Modele envoye. Attente...")
time.sleep(1)

# =============================================================================
# ETAPE 2: Fonction d'animation - mise a jour des positions
# =============================================================================

# Precalcul des positions en local
SWEEP = 0.53
L1 = math.sqrt((1237.7-563.3)**2 + (427.9-450.2)**2)
L2 = math.sqrt((1188.4-742.7)**2 + (531.6-543.8)**2)
Lc = math.sqrt((742.7-563.3)**2 + (543.8-450.2)**2)
ang_l = math.atan2(543.8-450.2, 742.7-563.3)
t1_0 = math.atan2(450.2-427.9, 563.3-1237.7)

C1=(25, 0); C2=(85, 355); C3=(785, 355); C4=(845, 0)
ax_d, ay_d = 563.3, 450.2
bx_d, by_d = 742.7, 543.8
Ax, Ay = 1237.7, 427.9
Bx, By = 1188.4, 531.6
DT = 355
DOOR_H = 2040

def compute_position(frac):
    """Calcule la position de la porte pour une fraction 0-1 de l'ouverture."""
    t1 = t1_0 - frac * math.pi * SWEEP
    axx = Ax + L1 * math.cos(t1)
    ayy = Ay + L1 * math.sin(t1)

    dx, dy = Bx - axx, By - ayy
    d = math.sqrt(dx*dx + dy*dy)
    if d > Lc + L2 + 0.01 or d < abs(Lc - L2) - 0.01:
        return None

    aa = (Lc*Lc - L2*L2 + d*d) / (2*d)
    h = math.sqrt(max(0, Lc*Lc - aa*aa))
    mx = axx + aa*dx/d; my = ayy + aa*dy/d
    px, py = -dy/d*h, dx/d*h
    bxx, byy = mx + px, my + py

    ang_w = math.atan2(byy - ayy, bxx - axx)
    door_ang = ang_w - ang_l
    co, si = math.cos(door_ang), math.sin(door_ang)
    tx = axx - (ax_d * co - ay_d * si)
    ty = ayy - (ax_d * si + ay_d * co)

    return {
        'tx': tx, 'ty': ty, 'angle_deg': math.degrees(door_ang),
        'arm_a': (axx, ayy), 'arm_b': (bxx, byy),
    }

def transform_2d(px, py, tx, ty, angle_rad):
    co, si = math.cos(angle_rad), math.sin(angle_rad)
    return (px*co - py*si + tx, px*si + py*co + ty)

def send_position(frac):
    """Envoie la mise a jour de position a FreeCAD."""
    pos = compute_position(frac)
    if pos is None:
        return

    tx, ty = pos['tx'], pos['ty']
    angle_rad = math.radians(pos['angle_deg'])
    angle_deg = pos['angle_deg']
    axx, ayy = pos['arm_a']
    bxx, byy = pos['arm_b']

    # Transformer les coins porte
    corners_world = [transform_2d(cx, cy, tx, ty, angle_rad) for cx, cy in [C1, C2, C3, C4]]

    # Transformer les pivots porte
    pa = transform_2d(ax_d, ay_d, tx, ty, angle_rad)
    pb = transform_2d(bx_d, by_d, tx, ty, angle_rad)
    pa_face = transform_2d(ax_d, DT, tx, ty, angle_rad)
    pb_face = transform_2d(bx_d, DT, tx, ty, angle_rad)

    # Bras angles et longueurs
    def arm_params(mx, my, px, py):
        ddx, ddy = px-mx, py-my
        return math.sqrt(ddx*ddx+ddy*ddy), math.degrees(math.atan2(ddy, ddx))
    l1, a1 = arm_params(Ax, Ay, pa[0], pa[1])
    l2, a2 = arm_params(Bx, By, pb[0], pb[1])

    # Pattes
    def patte_params(fx, fy, px, py):
        ddx, ddy = px-fx, py-fy
        return math.sqrt(ddx*ddx+ddy*ddy), math.degrees(math.atan2(ddy, ddx))
    lpa, apa = patte_params(pa_face[0], pa_face[1], pa[0], pa[1])
    lpb, apb = patte_params(pb_face[0], pb_face[1], pb[0], pb[1])

    code = f"""
import FreeCAD as App
import Part
import math

doc = App.ActiveDocument
DOOR_H = {DOOR_H}

# --- Porte: recreer la shape a la nouvelle position ---
corners = {corners_world}
wire = Part.makePolygon([App.Vector(x,y,0) for x,y in corners] + [App.Vector(corners[0][0],corners[0][1],0)])
face = Part.Face(wire)
shape = face.extrude(App.Vector(0,0,DOOR_H))
doc.getObject("Porte").Shape = shape

# --- Bras 1 ---
b1 = doc.getObject("Bras1")
b1.Height = {l1:.2f}
b1.Placement = App.Placement(
    App.Vector({Ax},{Ay},DOOR_H/2),
    App.Rotation(App.Vector(0,0,1),{a1:.2f}) * App.Rotation(App.Vector(0,1,0),90)
)

# --- Bras 2 ---
b2 = doc.getObject("Bras2")
b2.Height = {l2:.2f}
b2.Placement = App.Placement(
    App.Vector({Bx},{By},DOOR_H/2),
    App.Rotation(App.Vector(0,0,1),{a2:.2f}) * App.Rotation(App.Vector(0,1,0),90)
)

# --- Patte A ---
if {lpa:.2f} > 5:
    pa = doc.getObject("PatteA")
    pa.Height = {lpa:.2f}
    pa.Placement = App.Placement(
        App.Vector({pa_face[0]:.2f},{pa_face[1]:.2f},DOOR_H/2),
        App.Rotation(App.Vector(0,0,1),{apa:.2f}) * App.Rotation(App.Vector(0,1,0),90)
    )

# --- Patte B ---
if {lpb:.2f} > 5:
    pb = doc.getObject("PatteB")
    pb.Height = {lpb:.2f}
    pb.Placement = App.Placement(
        App.Vector({pb_face[0]:.2f},{pb_face[1]:.2f},DOOR_H/2),
        App.Rotation(App.Vector(0,0,1),{apb:.2f}) * App.Rotation(App.Vector(0,1,0),90)
    )

doc.recompute()
Gui.updateGui()
"""
    send(code)


# =============================================================================
# ETAPE 3: Boucle d'animation
# =============================================================================

print("Animation...")
print("  Ouverture...")
for i in range(61):
    frac = i / 60.0
    send_position(frac)
    angle = compute_position(frac)['angle_deg']
    if i % 10 == 0:
        print(f"    {i}/60: {angle:.1f}°")
    time.sleep(0.08)

print("  Pause ouverte...")
time.sleep(1.5)

print("  Fermeture...")
for i in range(60, -1, -1):
    frac = i / 60.0
    send_position(frac)
    time.sleep(0.08)

print("  Pause fermee...")
time.sleep(1.0)

print("\nAnimation terminee!")
print("Relancer pour rejouer, ou modifier le script pour boucler.")
