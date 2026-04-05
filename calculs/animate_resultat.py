#!/usr/bin/env python3
"""
Animation du meilleur resultat de l'optimisation.
Importe les parametres depuis optimisation_documentee.py.
"""
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
import os, sys

# Importer les parametres du script principal
sys.path.insert(0, os.path.dirname(__file__))
from optimisation_documentee import (
    OW, DT, DW, LWD, RWD, SBR, EFF_BACK,
    CADRE_HINGE, CADRE_TRAILING,
    TAPER_TRAILING, TAPER_HINGE,
    coins_porte, points_contour, transformer, verifier_collisions,
    simuler_mecanisme
)

# --- Parametres du meilleur resultat (coller depuis la sortie de l'optimisation) ---
Ax, Ay = 1246.1, 471.3
Bx, By = 1188.4, 586.1
ax_d, ay_d = 664.1, 426.3
bx_d, by_d = 766.2, 540.6
SWEEP = 0.55

a_loc = np.array([ax_d, ay_d])
b_loc = np.array([bx_d, by_d])
L1 = np.sqrt((Ax - ax_d)**2 + (Ay - ay_d)**2)
L2 = np.sqrt((Bx - bx_d)**2 + (By - by_d)**2)
Lc = np.sqrt((bx_d - ax_d)**2 + (by_d - ay_d)**2)
ang_l = np.arctan2(by_d - ay_d, bx_d - ax_d)
t1_0 = np.arctan2(ay_d - Ay, ax_d - Ax)
CORN = coins_porte()
EP = points_contour(15)

print(f"Porte: {DW}x{DT}mm trapeze (taper hinge={TAPER_HINGE}, trailing={TAPER_TRAILING})")
print(f"Coins: C1={CORN[0]}, C2={CORN[1]}, C3={CORN[2]}, C4={CORN[3]}")
print(f"A=({Ax:.0f},{Ay:.0f}) B=({Bx:.0f},{By:.0f})")
print(f"a=({ax_d:.0f},{DT}) b=({bx_d:.0f},{DT})")
print(f"L1={L1:.0f}mm L2={L2:.0f}mm Lc={Lc:.0f}mm")

# --- Simulation haute resolution ---
print("\nSimulation (400 pas)...")
best_mc = -1e6
best_pos = None

for br in [0, 1]:
    for di in [1, -1]:
        # Verif position fermee
        t1 = t1_0
        ax = Ax + L1 * np.cos(t1); ay = Ay + L1 * np.sin(t1)
        dx, dy = Bx - ax, By - ay; d = np.sqrt(dx*dx + dy*dy)
        if d > Lc + L2 + 0.01 or d < abs(Lc - L2) - 0.01: continue
        aa = (Lc*Lc - L2*L2 + d*d) / (2*d); h = np.sqrt(max(0, Lc*Lc - aa*aa))
        mx = ax + aa*dx/d; my = ay + aa*dy/d; px, py = -dy/d*h, dx/d*h
        bx_, by_ = (mx+px, my+py) if br == 0 else (mx-px, my-py)
        da0 = np.arctan2(by_-ay, bx_-ax) - ang_l
        co0, si0 = np.cos(da0), np.sin(da0)
        tx0 = ax - (a_loc[0]*co0 - a_loc[1]*si0)
        ty0 = ay - (a_loc[0]*si0 + a_loc[1]*co0)
        am = da0 % (2*np.pi)
        if am > np.pi: am -= 2*np.pi
        if abs(tx0) > 5 or abs(ty0) > 5 or (abs(am) > 0.1 and abs(am-2*np.pi) > 0.1 and abs(am+2*np.pi) > 0.1):
            continue

        pos = []; mc = 1e6; ok = True
        for i in range(401):
            f = i / 400; t1 = t1_0 + di * f * np.pi * SWEEP
            ax = Ax + L1*np.cos(t1); ay = Ay + L1*np.sin(t1)
            dx, dy = Bx-ax, By-ay; d = np.sqrt(dx*dx + dy*dy)
            if d > Lc+L2+0.01 or d < abs(Lc-L2)-0.01 or d < 1e-10: ok = False; break
            aa = (Lc*Lc-L2*L2+d*d)/(2*d); h = np.sqrt(max(0, Lc*Lc-aa*aa))
            mx = ax+aa*dx/d; my = ay+aa*dy/d; px, py = -dy/d*h, dx/d*h
            bx_, by_ = (mx+px, my+py) if br == 0 else (mx-px, my-py)
            da = np.arctan2(by_-ay, bx_-ax) - ang_l
            co, si = np.cos(da), np.sin(da)
            tx = ax - (a_loc[0]*co - a_loc[1]*si)
            ty = ay - (a_loc[0]*si + a_loc[1]*co)
            if i > 0:
                pts_w = transformer(EP, tx, ty, co, si)
                mc = min(mc, np.min(verifier_collisions(pts_w)))
            pos.append((tx, ty, da, ax, ay, bx_, by_))
        if not ok: continue

        tf, uf, af = pos[-1][:3]
        co, si = np.cos(af), np.sin(af)
        c_o = transformer(CORN, tf, uf, co, si)
        mc2 = mc
        # Position ouverte: porte derriere mur droit (x > OW)
        if np.min(c_o[:,0]) < OW - 5: mc2 = min(mc2, np.min(c_o[:,0]) - OW)
        # Dans l'espace dispo (x < OW + EFF_BACK)
        if np.max(c_o[:,0]) > OW + EFF_BACK - 5: mc2 = min(mc2, OW + EFF_BACK - np.max(c_o[:,0]))
        if abs(af) < np.radians(75): mc2 = min(mc2, -(90-np.degrees(abs(af)))*2)

        print(f"  br={br} di={di}: mc={mc2:.1f}mm rot={np.degrees(af):.1f}° "
              f"open_x=[{np.min(c_o[:,0]):.0f},{np.max(c_o[:,0]):.0f}]")
        if mc2 > best_mc:
            best_mc = mc2; best_pos = pos

if best_pos is None:
    print("ERREUR: aucune branche valide!"); sys.exit(1)

print(f"\nClearance: {best_mc:.1f}mm | {len(best_pos)} frames")
print(f"Rotation: {np.degrees(best_pos[-1][2]):.1f}°")

# --- Generation des frames ---
outdir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'exports')
fdir = os.path.join(outdir, 'frames_resultat')
os.makedirs(fdir, exist_ok=True)

n_frames = 60
idxs = np.linspace(0, len(best_pos)-1, n_frames, dtype=int)

for fi, pi in enumerate(idxs):
    tx, ty, ang, aax, aay, abx, aby = best_pos[pi]
    co, si = np.cos(ang), np.sin(ang)
    cw = transformer(CORN, tx, ty, co, si)

    if fi > 0:
        pts_w = transformer(EP, tx, ty, co, si)
        pt_cl = verifier_collisions(pts_w)
        min_cl = np.min(pt_cl)
    else:
        min_cl = 999
        pt_cl = np.ones(len(EP)) * 999
    collision = min_cl < 0 and fi > 0

    fig, ax = plt.subplots(figsize=(14, 16))
    ax.set_aspect('equal')
    ax.set_facecolor('#fafafa')

    # --- Murs (X inverse: gauche=trailing, droit=charnieres) ---
    # Mur gauche (trailing, x < 0, epaisseur LWD)
    ax.add_patch(patches.Rectangle((-250, 0), 250, LWD,
        fc='#c0c0c0', ec='black', lw=2, zorder=1))
    ax.text(-125, LWD/2, 'MUR\nGAUCHE', ha='center', va='center', fontsize=8, color='#555')
    # Mur droit (charnieres, x > OW, epaisseur RWD)
    ax.add_patch(patches.Rectangle((OW, 0), EFF_BACK+80, RWD,
        fc='#c0c0c0', ec='black', lw=2, zorder=1))
    ax.text(OW+100, RWD/2, 'MUR\nDROIT', ha='center', va='center', fontsize=8, color='#555')
    # Cuisine
    ax.add_patch(patches.Rectangle((-250,-250), OW+EFF_BACK+400, 250,
        fc='#ffe8cc', ec='#ddd', lw=1, zorder=0))
    # Espace derriere mur droit
    ax.add_patch(patches.Rectangle((OW, RWD), EFF_BACK, 1500,
        fc='#e8f5e9', ec='none', alpha=0.2, zorder=0))
    ax.axvline(x=OW+EFF_BACK, color='red', ls='--', lw=1.5, alpha=0.4)
    # Cadres (deux cotes)
    if CADRE_TRAILING > 0:
        ax.add_patch(patches.Rectangle((0, 0), CADRE_TRAILING, DT,
            fc='#8d6e63', ec='black', lw=1.5, alpha=0.4, zorder=2))
        ax.text(CADRE_TRAILING/2, DT/2, f'{CADRE_TRAILING}', ha='center', va='center',
                fontsize=7, color='white', fontweight='bold', zorder=3)
    if CADRE_HINGE > 0:
        ax.add_patch(patches.Rectangle((OW - CADRE_HINGE, 0), CADRE_HINGE, DT,
            fc='#8d6e63', ec='black', lw=1.5, alpha=0.4, zorder=2))
        ax.text(OW - CADRE_HINGE/2, DT/2, f'{CADRE_HINGE}', ha='center', va='center',
                fontsize=7, color='white', fontweight='bold', zorder=3)

    # Labels
    ax.text(OW/2, -130, 'CUISINE', ha='center', fontsize=16, fontweight='bold', color='#c65100')
    ax.text(OW/2, 1100, 'BUANDERIE', ha='center', fontsize=18, fontweight='bold', color='#1565c0')
    ax.annotate('', xy=(0,-40), xytext=(OW,-40),
                arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))
    ax.text(OW/2, -65, f'Ouverture {OW}mm', ha='center', fontsize=10)

    # --- Porte (trapeze) ---
    door_fc = '#ef5350' if collision else '#66bb6a'
    ax.add_patch(plt.Polygon(cw, fc=door_fc, ec='black', alpha=0.55, lw=2.5, zorder=5))

    # Points de collision
    if collision:
        pts_w = transformer(EP, tx, ty, co, si)
        coll_mask = pt_cl < 0
        if np.any(coll_mask):
            ax.scatter(pts_w[coll_mask,0], pts_w[coll_mask,1], c='red', s=50,
                       zorder=8, marker='x', linewidths=3)

    # Etageres (lignes dans la porte)
    for frac in [0.25, 0.5, 0.75]:
        # Interpoler entre les aretes C1-C2 et C4-C3
        p1 = CORN[0]*(1-frac) + CORN[1]*frac  # sur arete C1-C2
        p2 = CORN[3]*(1-frac) + CORN[2]*frac  # sur arete C4-C3
        p1w = transformer(p1.reshape(1,-1), tx, ty, co, si)[0]
        p2w = transformer(p2.reshape(1,-1), tx, ty, co, si)[0]
        ax.plot([p1w[0],p2w[0]], [p1w[1],p2w[1]], 'k-', lw=0.5, alpha=0.2, zorder=6)

    # Coins
    for ci, (cc, nm) in enumerate(zip(['#d32f2f','#1565c0','#2e7d32','#e65100'],
                                       ['C1','C2','C3','C4'])):
        ax.plot(cw[ci,0], cw[ci,1], 'o', color=cc, ms=7, zorder=9,
                markeredgecolor='black', markeredgewidth=1)
        ox = 20 if ci < 2 else -30
        ax.text(cw[ci,0]+ox, cw[ci,1]+20, nm, fontsize=8, color=cc, fontweight='bold', zorder=9)

    # --- Bras ---
    aw = transformer(a_loc.reshape(1,-1), tx, ty, co, si)[0]
    bw = transformer(b_loc.reshape(1,-1), tx, ty, co, si)[0]
    ax.plot([Ax,aw[0]], [Ay,aw[1]], color='#c62828', lw=4, alpha=0.8, zorder=4, solid_capstyle='round')
    ax.plot([Bx,bw[0]], [By,bw[1]], color='#1565c0', lw=4, alpha=0.8, zorder=4, solid_capstyle='round')
    # Pivots fixes
    ax.plot(Ax, Ay, 'rs', ms=12, zorder=10, markeredgecolor='black', markeredgewidth=1.5)
    ax.plot(Bx, By, 'b^', ms=12, zorder=10, markeredgecolor='black', markeredgewidth=1.5)
    ax.text(Ax-60, Ay+15, f'A', fontsize=10, fontweight='bold', color='#c62828')
    ax.text(Bx-60, By+15, f'B', fontsize=10, fontweight='bold', color='#1565c0')
    # Pivots mobiles
    ax.plot(aw[0], aw[1], 'o', color='#c62828', ms=7, zorder=10, markeredgecolor='black')
    ax.plot(bw[0], bw[1], 'o', color='#1565c0', ms=7, zorder=10, markeredgecolor='black')

    # --- Trajectoires des coins ---
    for ci, cc in enumerate(['#d32f2f','#1565c0','#2e7d32','#e65100']):
        traj = np.array([transformer(CORN[ci:ci+1], *p[:2], np.cos(p[2]), np.sin(p[2]))[0]
                         for p in best_pos[:pi+1]])
        if len(traj) > 1:
            ax.plot(traj[:,0], traj[:,1], color=cc, lw=1.5, alpha=0.4, zorder=3)

    # --- Info ---
    deg = np.degrees(ang)
    status = "COLLISION" if collision else "OK"
    sc = '#d32f2f' if collision else '#2e7d32'
    cl_text = f'{min_cl:.0f}mm' if fi > 0 else 'fermee'
    info = f"Angle: {deg:.1f}°  |  Clearance: {cl_text}  |  {status}"
    ax.text(OW/2, -190, info, ha='center', fontsize=13, fontfamily='monospace',
            fontweight='bold', color=sc,
            bbox=dict(boxstyle='round,pad=0.4', fc='white', ec=sc, alpha=0.9))

    ax.set_title(
        f'Porte {DW}x{DT}mm trapeze (taper h={TAPER_HINGE}/t={TAPER_TRAILING}) + cadres {CADRE_HINGE}/{CADRE_TRAILING}mm\n'
        f'4-bar pivots arriere | Bras {L1:.0f}/{L2:.0f}mm | Clearance min {best_mc:.0f}mm',
        fontsize=12, fontweight='bold', color='#333')

    ax.set_xlim(-300, OW+EFF_BACK+120)
    ax.set_ylim(-260, max(1300, Ay+100, By+100))
    ax.grid(True, alpha=0.15)
    plt.tight_layout()
    plt.savefig(os.path.join(fdir, f'f_{fi:03d}.png'), dpi=72, bbox_inches='tight')
    plt.close()

    if fi % 10 == 0:
        print(f"  Frame {fi}/{n_frames}: {deg:.1f}° cl={cl_text}")

# --- GIF ---
print("\nCreation du GIF...")
frames = [Image.open(os.path.join(fdir, f'f_{i:03d}.png')) for i in range(n_frames)]
frames_loop = frames[:1]*5 + frames + frames[-1:]*5 + frames[-2:0:-1]
gif = os.path.join(outdir, 'RESULTAT_animation.gif')
frames_loop[0].save(gif, save_all=True, append_images=frames_loop[1:], duration=120, loop=0)
print(f"\nGIF: {gif}")
print(f"Ouvrir: file://{gif}")
