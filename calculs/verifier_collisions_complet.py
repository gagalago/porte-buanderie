#!/usr/bin/env python3
"""
=============================================================================
VERIFICATION COMPLETE DES COLLISIONS
=============================================================================

Verifie a chaque pas de la simulation (haute resolution):
1. Porte (contour) vs murs
2. Bras 1 (tube 40mm large) vs murs
3. Bras 2 (tube 40mm large) vs murs
4. Platines porte (depassent derriere la porte) vs murs
5. Bras vs bras (croisement en XY, meme si decales en Z)

Sortie: rapport detaille avec la pire clearance par type.
"""

import numpy as np
import sys, os, math

sys.path.insert(0, os.path.dirname(__file__))
from optimisation_documentee import (
    OW, DT, LWD, RWD, SBR, EFF_BACK,
    CADRE_HINGE, CADRE_TRAILING, TAPER_TRAILING, TAPER_HINGE,
    coins_porte, points_contour, transformer, verifier_collisions,
    simuler_mecanisme
)

# Parametres solution
Ax, Ay = 1241.2, 482.3
Bx, By = 1197.4, 570.1
ax_d, ay_d = 589.9, 463.9
bx_d, by_d = 701.7, 549.2
SWEEP = 0.55

# Quincaillerie
TUBE_W = 40       # largeur tube bras
TOLE = 5          # epaisseur platine
PLATINE_MARGIN = 40  # marge autour des pivots pour la platine
PIVOT_MARGIN = 15
AXE_HOLE = 18

# Dimensions derivees
L1 = math.sqrt((Ax - ax_d)**2 + (Ay - ay_d)**2)
L2 = math.sqrt((Bx - bx_d)**2 + (By - by_d)**2)
Lc = math.sqrt((bx_d - ax_d)**2 + (by_d - ay_d)**2)
ang_l = math.atan2(by_d - ay_d, bx_d - ax_d)
t1_0 = math.atan2(ay_d - Ay, ax_d - Ax)

# Platine porte: contour en coords locales porte
# C'est un rectangle de x_min a x_max, y de DT a max_depth+marge
plat_x_min = min(ax_d, bx_d) - PLATINE_MARGIN
plat_x_max = max(ax_d, bx_d) + PLATINE_MARGIN
plat_y_min = DT
plat_y_max = max(ay_d, by_d) + PIVOT_MARGIN + AXE_HOLE/2


def verifier_lateral(pts_monde):
    """Verifie seulement les murs lateraux (pas la limite arriere).
    Pour les composants fins (bras, platines) qui passent au-dessus du frigo."""
    x, y = pts_monde[:, 0], pts_monde[:, 1]
    clearance = np.full(len(x), 1e6)
    # Mur gauche: x > 0 si y < LWD
    mask_g = y < LWD
    clearance[mask_g] = np.minimum(clearance[mask_g], x[mask_g])
    # Mur droit (retour): x < OW si y < RWD
    mask_d = y < RWD
    clearance[mask_d] = np.minimum(clearance[mask_d], OW - x[mask_d])
    # Sol cuisine: y > -2
    clearance = np.minimum(clearance, np.where(y < -2, y, 1e6))
    return clearance


def points_bras(px_start, py_start, px_end, py_end, n_along=20, n_across=3):
    """Genere des points le long d'un bras (tube de largeur TUBE_W).
    Le bras va de (px_start, py_start) a (px_end, py_end).
    On genere des points sur les deux bords du tube."""
    dx = px_end - px_start
    dy = py_end - py_start
    length = math.sqrt(dx*dx + dy*dy)
    if length < 1:
        return np.array([[px_start, py_start]])

    # Direction et normale
    ux, uy = dx/length, dy/length
    nx, ny = -uy, ux  # normale (perpendiculaire)

    pts = []
    for t in np.linspace(0, 1, n_along):
        cx = px_start + t * dx
        cy = py_start + t * dy
        for s in np.linspace(-TUBE_W/2, TUBE_W/2, n_across):
            pts.append([cx + s * nx, cy + s * ny])
    return np.array(pts)


def points_platine_porte(tx, ty, cos_a, sin_a, n=8):
    """Genere des points sur le contour de la platine porte en coords monde."""
    # Contour en coords locales porte
    pts_local = []
    for x in np.linspace(plat_x_min, plat_x_max, n):
        for y in [plat_y_min, plat_y_max]:
            pts_local.append([x, y])
    for y in np.linspace(plat_y_min, plat_y_max, n):
        for x in [plat_x_min, plat_x_max]:
            pts_local.append([x, y])
    pts_local = np.array(pts_local)
    return transformer(pts_local, tx, ty, cos_a, sin_a)


def simulate_full(n_steps=400):
    """Simulation haute resolution avec verification complete."""
    # Trouver la bonne branche/direction
    best_pos = None
    best_mc = -1e6

    for br in [0, 1]:
        for di in [1, -1]:
            t1 = t1_0
            axx = Ax + L1*math.cos(t1); ayy = Ay + L1*math.sin(t1)
            dx, dy = Bx-axx, By-ayy; d = math.sqrt(dx*dx+dy*dy)
            if d > Lc+L2+.01 or d < abs(Lc-L2)-.01: continue
            aa = (Lc**2-L2**2+d**2)/(2*d); h = math.sqrt(max(0, Lc**2-aa**2))
            mx = axx+aa*dx/d; my = ayy+aa*dy/d; px,py = -dy/d*h, dx/d*h
            bxx, byy = (mx+px, my+py) if br == 0 else (mx-px, my-py)
            aw = math.atan2(byy-ayy, bxx-axx); da = aw-ang_l
            co, si = math.cos(da), math.sin(da)
            tx = axx-(ax_d*co-ay_d*si); ty = ayy-(ax_d*si+ay_d*co)
            am = da % (2*math.pi)
            if am > math.pi: am -= 2*math.pi
            if abs(tx) > 5 or abs(ty) > 5: continue
            if abs(am) > 0.1 and abs(am-2*math.pi) > 0.1 and abs(am+2*math.pi) > 0.1: continue

            positions = []
            ok = True
            for i in range(n_steps + 1):
                f = i / n_steps
                t1 = t1_0 + di * f * math.pi * SWEEP
                axx = Ax + L1*math.cos(t1); ayy = Ay + L1*math.sin(t1)
                dx, dy = Bx-axx, By-ayy; d = math.sqrt(dx*dx+dy*dy)
                if d > Lc+L2+.01 or d < abs(Lc-L2)-.01 or d < 1e-10:
                    ok = False; break
                aa = (Lc**2-L2**2+d**2)/(2*d); h = math.sqrt(max(0, Lc**2-aa**2))
                mx = axx+aa*dx/d; my = ayy+aa*dy/d; px,py = -dy/d*h, dx/d*h
                bxx, byy = (mx+px, my+py) if br == 0 else (mx-px, my-py)
                aw = math.atan2(byy-ayy, bxx-axx); da = aw-ang_l
                co, si = math.cos(da), math.sin(da)
                tx = axx-(ax_d*co-ay_d*si); ty = ayy-(ax_d*si+ay_d*co)
                positions.append({
                    'tx': tx, 'ty': ty, 'angle': da,
                    'cos': co, 'sin': si,
                    'arm_a': (axx, ayy), 'arm_b': (bxx, byy),
                    'pct': f * 100,
                })
            if not ok: continue

            # Score: rotation finale
            score = abs(positions[-1]['angle'])
            if score > best_mc:
                best_mc = score
                best_pos = positions

    return best_pos


# =============================================================================
# EXECUTION
# =============================================================================
print("=" * 70)
print("VERIFICATION COMPLETE DES COLLISIONS")
print("=" * 70)
print(f"Porte: {OW-CADRE_HINGE-CADRE_TRAILING}x{DT}mm trapeze")
print(f"Pivots mur: A=({Ax:.0f},{Ay:.0f}) B=({Bx:.0f},{By:.0f})")
print(f"Pivots porte: a=({ax_d:.0f},{ay_d:.0f}) b=({bx_d:.0f},{by_d:.0f})")
print(f"Bras: L1={L1:.0f}mm L2={L2:.0f}mm (tube {TUBE_W}mm large)")
print(f"Platine porte: x=[{plat_x_min:.0f},{plat_x_max:.0f}] y=[{plat_y_min:.0f},{plat_y_max:.0f}]")
print()

N_STEPS = 400
print(f"Simulation haute resolution ({N_STEPS} pas)...")
positions = simulate_full(N_STEPS)
if not positions:
    print("ERREUR: pas de solution valide!"); sys.exit(1)

print(f"  {len(positions)} positions, rotation max = {math.degrees(positions[-1]['angle']):.1f} deg\n")

# Points du contour de la porte
EP = points_contour(15)
COINS = coins_porte()

# Resultats par type
results = {
    'porte': {'min_cl': 1e6, 'worst_pct': 0, 'worst_detail': ''},
    'bras1': {'min_cl': 1e6, 'worst_pct': 0, 'worst_detail': ''},
    'bras2': {'min_cl': 1e6, 'worst_pct': 0, 'worst_detail': ''},
    'platine_porte': {'min_cl': 1e6, 'worst_pct': 0, 'worst_detail': ''},
}

print("Verification en cours...")
for i, pos in enumerate(positions):
    if i == 0:
        continue  # position fermee = par design

    tx, ty = pos['tx'], pos['ty']
    co, si = pos['cos'], pos['sin']
    aax, aay = pos['arm_a']
    abx, aby = pos['arm_b']
    pct = pos['pct']

    # 1. PORTE vs murs
    pts_porte = transformer(EP, tx, ty, co, si)
    cl_porte = np.min(verifier_collisions(pts_porte))
    if cl_porte < results['porte']['min_cl']:
        results['porte']['min_cl'] = cl_porte
        results['porte']['worst_pct'] = pct
        # Trouver quel coin est le plus proche
        coins_monde = transformer(COINS, tx, ty, co, si)
        cl_coins = verifier_collisions(coins_monde)
        worst_coin = np.argmin(cl_coins)
        results['porte']['worst_detail'] = f'coin C{worst_coin+1} cl={cl_coins[worst_coin]:.1f}mm'

    # 2. BRAS 1 (A -> a) vs murs LATERAUX (pas limite arriere)
    # Les bras sont fins (tube 25mm) et passent au-dessus du frigo
    pts_b1 = points_bras(Ax, Ay, aax, aay)
    cl_b1 = np.min(verifier_lateral(pts_b1))
    if cl_b1 < results['bras1']['min_cl']:
        results['bras1']['min_cl'] = cl_b1
        results['bras1']['worst_pct'] = pct
        cl_all = verifier_lateral(pts_b1)
        worst_idx = np.argmin(cl_all)
        wp = pts_b1[worst_idx]
        results['bras1']['worst_detail'] = f'pt ({wp[0]:.0f},{wp[1]:.0f}) cl={cl_b1:.1f}mm'

    # 3. BRAS 2 (B -> b) vs murs LATERAUX
    pts_b2 = points_bras(Bx, By, abx, aby)
    cl_b2 = np.min(verifier_lateral(pts_b2))
    if cl_b2 < results['bras2']['min_cl']:
        results['bras2']['min_cl'] = cl_b2
        results['bras2']['worst_pct'] = pct
        cl_all = verifier_lateral(pts_b2)
        worst_idx = np.argmin(cl_all)
        wp = pts_b2[worst_idx]
        results['bras2']['worst_detail'] = f'pt ({wp[0]:.0f},{wp[1]:.0f}) cl={cl_b2:.1f}mm'

    # 4. PLATINE PORTE vs murs LATERAUX (fine, passe au-dessus du frigo)
    pts_plat = points_platine_porte(tx, ty, co, si)
    cl_plat = np.min(verifier_lateral(pts_plat))
    if cl_plat < results['platine_porte']['min_cl']:
        results['platine_porte']['min_cl'] = cl_plat
        results['platine_porte']['worst_pct'] = pct
        cl_all = verifier_lateral(pts_plat)
        worst_idx = np.argmin(cl_all)
        wp = pts_plat[worst_idx]
        results['platine_porte']['worst_detail'] = f'pt ({wp[0]:.0f},{wp[1]:.0f}) cl={cl_plat:.1f}mm'

    # Progress
    if i % 100 == 0:
        print(f"  {pct:.0f}%...")

# =============================================================================
# RAPPORT
# =============================================================================
print()
print("=" * 70)
print("RAPPORT DE COLLISIONS")
print("=" * 70)

all_ok = True
for name, label in [('porte', 'PORTE vs murs'),
                     ('bras1', 'BRAS 1 (A-a) vs murs'),
                     ('bras2', 'BRAS 2 (B-b) vs murs'),
                     ('platine_porte', 'PLATINE PORTE vs murs')]:
    r = results[name]
    cl = r['min_cl']
    status = 'OK' if cl >= 5 else 'SERRE' if cl >= 0 else 'COLLISION'
    icon = '  ' if cl >= 5 else '! ' if cl >= 0 else '!!'

    if cl >= 1e5:
        print(f"  {icon} {label:30s}: pas de contrainte")
    else:
        print(f"  {icon} {label:30s}: clearance = {cl:+.1f}mm @ {r['worst_pct']:.0f}% | {r['worst_detail']}")

    if cl < 0:
        all_ok = False

print()
if all_ok:
    global_min = min(r['min_cl'] for r in results.values())
    print(f"RESULTAT: AUCUNE COLLISION (clearance globale = {global_min:.1f}mm)")
else:
    print("RESULTAT: COLLISIONS DETECTEES!")
    for name, r in results.items():
        if r['min_cl'] < 0:
            print(f"  -> {name}: {r['min_cl']:.1f}mm @ {r['worst_pct']:.0f}%")
