#!/usr/bin/env python3
"""
=============================================================================
OPTIMISATION D'UN MECANISME 4-BAR LINKAGE POUR PORTE EPAISSE
=============================================================================

PROBLEME:
    Une porte epaisse (355mm) doit pivoter dans une ouverture de 870mm.
    La diagonale de la porte (940mm) depasse l'ouverture de 70mm.
    Un pivot unique ne fonctionne pas: le coin de la porte heurte le mur.

SOLUTION:
    Un mecanisme a 4 barres (4-bar linkage) avec 2 bras articules qui
    relient le mur a la porte. Ce mecanisme combine translation et rotation,
    permettant a la porte de se decaler lateralement pendant qu'elle pivote.

=============================================================================
VUE DE DESSUS (plan) - Systeme de coordonnees
=============================================================================

    Vu depuis au-dessus, oriente comme quand on regarde depuis la cuisine:
    - X va de gauche (0) a droite (870)
    - Y va de la cuisine (0) vers la buanderie (positif)

    Y (vers buanderie)
    ^
    |
    |   Buanderie (y > 355 cote gauche, y > 425 cote droit)
    |
    +------  MUR GAUCHE  ---  OUVERTURE  ---  MUR DROIT  ------+
    |  (x < 0)           (x: 0 a 870)        (x > 870)        |
    |  (y: 0-355)                             (y: 0-425)       |
    +--- y = 0 (face cuisine) ---------------------------------+-------> X
    |
    |   Cuisine (y < 0)

    Mur GAUCHE (x < 0) : cote trailing (oppose aux charnieres), epaisseur 355mm
    Mur DROIT (x > 870) : cote charnieres, epaisseur 425mm
    Espace derriere le mur droit : 380mm dans la buanderie (x > 870, y > 425)

    Porte fermee:
        C1 = (CADRE_TRAILING, 0)     coin gauche, face cuisine (trailing)
        C2 = (CADRE_TRAILING+TAPER, DT)  coin gauche, face buanderie
        C3 = (OW-CADRE_HINGE-TAPER, DT)  coin droit, face buanderie
        C4 = (OW-CADRE_HINGE, 0)    coin droit, face cuisine (charnieres)

=============================================================================
LE MECANISME 4-BAR LINKAGE
=============================================================================

    2 pivots FIXES sur le mur (cote buanderie du mur droit):
        A = (Ax, Ay)    pivot fixe haut
        B = (Bx, By)    pivot fixe bas

    2 pivots MOBILES sur la face arriere de la porte (y = DT en coords locales):
        a = (ax_door, DT)    pivot porte, position x variable
        b = (bx_door, DT)    pivot porte, position x variable

    2 BRAS rigides:
        Bras 1: relie A a 'a' (longueur L1 = distance(A, a_ferme))
        Bras 2: relie B a 'b' (longueur L2 = distance(B, b_ferme))

    Schema (porte fermee, vue de dessus):

        Buanderie
                    A ----bras1---- a          b ----bras2---- B
                    (mur)           |__________|               (mur)
                                    |  PORTE   |
                                    |  (face   |
                                    | arriere) |
                                    C2---------C3
                                    |          |
                                    |          |
                                    C1---------C4
        Cuisine

    Quand le bras 1 tourne autour de A, il tire le point 'a' sur la porte.
    Le bras 2 contraint le point 'b'. La porte (corps rigide) suit le
    mouvement impose par les deux bras, se translatent ET pivotant.

=============================================================================
PARAMETRES FIXES (geometrie de la piece)
=============================================================================
"""

import numpy as np
from scipy.optimize import differential_evolution

# --- Dimensions de la piece (mesurees, en mm) ---
OW = 870          # Largeur de l'ouverture entre cuisine et buanderie
LWD = 355         # Epaisseur du mur GAUCHE (x < 0, cote trailing)
RWD = 425         # Epaisseur du mur DROIT (x > 870, cote charnieres)
SBR = 380         # Espace disponible derriere le mur droit (dans la buanderie)

# --- Dimensions de la porte (en mm) ---
DT = 355          # Epaisseur de la porte (= epaisseur mur gauche)
CADRE_HINGE = 25  # Cadre cote charnieres (droit)
CADRE_TRAILING = 25  # Cadre cote trailing (gauche)
DW = OW - CADRE_HINGE - CADRE_TRAILING  # = 750mm, largeur porte cote cuisine
CADRE = CADRE_HINGE + CADRE_TRAILING  # = 120mm total

# --- Forme trapeze de la porte (en mm) ---
# La porte peut etre un trapeze: pleine largeur cote cuisine, retreciee cote buanderie.
# On peut retrecir les DEUX coins buanderie independamment.
#
# TAPER_TRAILING = retrecissement du coin C3 (gauche-buanderie, cote trailing)
# TAPER_HINGE    = retrecissement du coin C2 (droit-buanderie, cote charnieres)
#
# 0 = pas de retrecissement de ce coin (angle droit)
# ex: TAPER_TRAILING=60 et TAPER_HINGE=30 donne:
#
#   Vue de dessus:
#
#      C2──────────────C3          y = DT (face buanderie, retreciee)
#      /                \          C2 est a x = TAPER_HINGE
#     /                  \         C3 est a x = DW - TAPER_TRAILING
#    /      PORTE         \
#   C1─────────────────────C4      y = 0 (face cuisine, pleine largeur)
#   x=0                  x=DW
#
# Cela reduit le cercle circonscrit a la porte (= le vrai "probleme diagonal")
# Un rectangle DW x DT a un cercle de rayon sqrt(DW²+DT²)/2
# Un trapeze a un cercle plus petit car les coins buanderie sont rentres.
#
TAPER_TRAILING = 60   # retrecissement coin C3 (gauche-buanderie)
TAPER_HINGE = 60      # retrecissement coin C2 (droit-buanderie)

# --- Modifications acceptees sur les murs ---
EXTRA_BACK = 0    # Pas d'espace supplementaire (frigo juste derriere)
EFF_BACK = SBR + EXTRA_BACK  # = 380mm, espace effectif derriere

# --- Parametres de simulation ---
N_STEPS = 50     # Nombre de pas de simulation (plus = plus precis mais plus lent)

"""
=============================================================================
PARAMETRES A OPTIMISER (6 variables)
=============================================================================

Ce sont les positions des 4 pivots du mecanisme:

1. Ax : position X du pivot fixe A sur le mur
         CONTRAINTE: doit etre SUR le mur droit, face buanderie
         Plage: de -380 (fond de l'espace derriere) a +30 (dans l'ouverture)

2. Ay : position Y du pivot fixe A sur le mur
         CONTRAINTE: doit etre SUR le mur droit
         Plage: de 395 a 455 (autour de y=425, face buanderie du mur droit)

3. Bx : position X du pivot fixe B sur le mur
         CONTRAINTE: doit etre SUR le mur droit (face buanderie OU retour)
         Plage: de -30 a +30 (pres du coin de l'ouverture)

4. By : position Y du pivot fixe B sur le mur
         CONTRAINTE: doit etre SUR le mur droit
         Plage: de 0 a 455 (le long du retour ou de la face buanderie)

5. ax_door : position X du pivot 'a' sur/derriere la face arriere de la porte
         Plage: de TAPER_HINGE+20 a DW-TAPER_TRAILING-20

6. bx_door : position X du pivot 'b' sur/derriere la face arriere de la porte
         Plage: de TAPER_HINGE+20 a DW-TAPER_TRAILING-20

7. ay_door : position Y du pivot 'a' (profondeur derriere la porte)
         DT = sur la face arriere, DT+200 = 20cm dans la buanderie (patte)
         Plage: de DT a DT+200

8. by_door : position Y du pivot 'b' (profondeur derriere la porte)
         Plage: de DT a DT+200

9. sweep : fraction de pi que parcourt le bras 1 pendant l'ouverture
         0.4 = 72 degres, 0.8 = 144 degres, 1.0 = 180 degres
         Plage: de 0.3 a 1.2

Les LONGUEURS des bras ne sont PAS des variables:
    L1 = distance(A, a_en_position_fermee) -- calculee automatiquement
    L2 = distance(B, b_en_position_fermee) -- calculee automatiquement
"""

# --- Contrainte hardware: clearance pivot <-> surface ---
# Le pivot doit etre assez loin de la surface (mur ou porte) pour loger:
#   - La tole de la platine (fond plaque contre la surface)
#   - Le demi-tube du bras (le bras pivote autour de l'axe)
#   - Un jeu de fonctionnement
# Dimensions quincaillerie:
TOLE_PLATINE = 5     # epaisseur tole platine (mm)
TUBE_BRAS_W = 40     # largeur tube bras (mm) - c'est la dimension qui peut frotter
JEU_PIVOT = 5        # jeu de fonctionnement (mm)
MIN_PIVOT_CLEARANCE = TOLE_PLATINE + TUBE_BRAS_W / 2 + JEU_PIVOT  # = 30mm

# Bornes pour l'optimisation (9 variables)
# Mur droit (charnieres) est a x > OW (= x > 870)
# Les pivots mur sont sur la face buanderie du mur droit: x de OW a OW+SBR
# Les pivots porte sont entre C2.x et C3.x sur la face arriere
C2X = CADRE_TRAILING + TAPER_TRAILING        # x du coin C2
C3X = OW - CADRE_HINGE - TAPER_HINGE         # x du coin C3
BOUNDS = [
    (OW - 30, OW + SBR),                    # Ax: sur/pres du mur droit
    (RWD + MIN_PIVOT_CLEARANCE, RWD + 200),  # Ay: au moins 30mm de la face mur
    (OW - 30, OW + SBR),                    # Bx: sur/pres du mur droit
    (RWD + MIN_PIVOT_CLEARANCE, RWD + 200),  # By: au moins 30mm de la face mur
    (C2X + 10, C3X - 10),                   # ax_door: x entre C2 et C3
    (C2X + 10, C3X - 10),                   # bx_door: x entre C2 et C3
    (DT + MIN_PIVOT_CLEARANCE, DT + 200),    # ay_door: au moins 30mm de la face porte
    (DT + MIN_PIVOT_CLEARANCE, DT + 200),    # by_door: au moins 30mm de la face porte
    (0.3, 1.2),                          # sweep: fraction de pi pour rotation bras 1
]


def coins_porte():
    """Les 4 coins de la porte en coordonnees monde (porte fermee).
    X inversee: gauche=trailing (x petit), droit=charnieres (x grand).
    La porte occupe x de CADRE_TRAILING a OW-CADRE_HINGE."""
    x_left = CADRE_TRAILING                     # bord gauche (trailing)
    x_right = OW - CADRE_HINGE                  # bord droit (charnieres)
    return np.array([
        [x_left, 0],                            # C1: gauche-cuisine (trailing)
        [x_left + TAPER_TRAILING, DT],           # C2: gauche-buanderie (retreci)
        [x_right - TAPER_HINGE, DT],             # C3: droit-buanderie (retreci)
        [x_right, 0],                            # C4: droit-cuisine (charnieres)
    ], dtype=float)


def points_contour(n_par_arete=10):
    """Points repartis sur le contour de la porte (pour verifier les collisions)."""
    coins = coins_porte()
    pts = []
    for i in range(4):
        for t in np.linspace(0, 1, n_par_arete, endpoint=False):
            pts.append(coins[i] * (1 - t) + coins[(i + 1) % 4] * t)
    return np.array(pts)


def transformer(pts, tx, ty, cos_a, sin_a):
    """Applique rotation + translation aux points.
    pts: (N,2) points en coords locales porte
    tx, ty: translation
    cos_a, sin_a: cos et sin de l'angle de rotation
    Retourne: (N,2) points en coords monde
    """
    return np.column_stack([
        pts[:, 0] * cos_a - pts[:, 1] * sin_a + tx,
        pts[:, 0] * sin_a + pts[:, 1] * cos_a + ty,
    ])


def verifier_collisions(pts_monde):
    """
    Calcule la clearance (distance aux murs) pour chaque point.

    Retourne un array de distances:
        > 0 : le point est dans l'espace libre (OK)
        < 0 : le point est DANS un mur (COLLISION)
        = 0 : le point touche un mur

    Les murs verifies (axe X inverse: gauche=0, droit=870):
        1. Mur gauche (trailing): x > 0 requis si y < LWD (355mm)
        2. Mur droit (charnieres): x < OW requis si y < RWD (425mm)
        3. Limite arriere mur droit: x < OW + EFF_BACK
        4. Sol cuisine: y > -2 requis (la porte peut affleurer a y=0)
    """
    x, y = pts_monde[:, 0], pts_monde[:, 1]
    clearance = np.full(len(x), 1e6)  # commence a +infini (tout OK)

    # 1. Mur gauche (trailing, x < 0): pour y < LWD, x doit etre > 0
    dans_zone_mur_gauche = y < LWD
    clearance[dans_zone_mur_gauche] = np.minimum(
        clearance[dans_zone_mur_gauche],
        x[dans_zone_mur_gauche]
    )

    # 2. Mur droit (charnieres, x > OW): pour y < RWD, x doit etre < OW
    dans_zone_mur_droit = y < RWD
    clearance = np.where(
        dans_zone_mur_droit,
        np.minimum(clearance, OW - x),
        clearance
    )

    # 3. Limite arriere mur droit: x < OW + EFF_BACK (espace derriere)
    np.minimum(clearance, OW + EFF_BACK - x, out=clearance)

    # 4. Sol cuisine: y doit etre > -2mm (tolerance pour affleurage)
    clearance = np.minimum(clearance, np.where(y < -2, y, 1e6))

    return clearance


def simuler_mecanisme(Ax, Ay, Bx, By, ax_door, bx_door, ay_door=DT, by_door=DT, sweep=0.8):
    """
    Simule le mouvement du 4-bar linkage.

    Retourne: (clearance_min, positions)
        clearance_min: la pire clearance sur tout le trajet (> 0 = OK)
        positions: liste de (tx, ty, angle, arm_ax, arm_ay, arm_bx, arm_by)
                   pour chaque pas de la simulation

    Les pivots porte sont a (ax_door, ay_door) et (bx_door, by_door) en coords
    locales de la porte. ay_door et by_door peuvent depasser DT (= pattes qui
    sortent de la face arriere de la porte dans la buanderie).
    """
    # Pivots sur la porte (coordonnees locales)
    # ay_door >= DT : sur la face arriere ou sur une patte derriere
    a_local = np.array([ax_door, ay_door])
    b_local = np.array([bx_door, by_door])

    # Bornes de la platine porte en coords locales (pour collision check)
    plat_margin = 40  # marge autour des pivots
    plat_x_min = min(ax_door, bx_door) - plat_margin
    plat_x_max = max(ax_door, bx_door) + plat_margin

    # Longueur du coupler (distance entre les 2 pivots porte)
    Lc = np.sqrt((bx_door - ax_door)**2 + (by_door - ay_door)**2)
    if Lc < 50:
        return -9999, None

    # Longueurs des bras (calculees a partir de la position fermee)
    # En position fermee, a_local en coords monde = (ax_door, ay_door)
    L1 = np.sqrt((Ax - ax_door)**2 + (Ay - ay_door)**2)
    L2 = np.sqrt((Bx - bx_door)**2 + (By - by_door)**2)
    if L1 < 30 or L2 < 30 or L1 > 800 or L2 > 800:
        return -9999, None

    # Direction du coupler en coords locales (a -> b)
    ang_local = np.arctan2(by_door - ay_door, bx_door - ax_door)

    # Angle initial du bras 1 (de A vers a_ferme)
    theta1_initial = np.arctan2(ay_door - Ay, ax_door - Ax)

    coins = coins_porte()
    points = points_contour(10)

    meilleur_resultat = -9999
    meilleures_positions = None

    # Essayer les 4 combinaisons branche/direction
    for branche in [0, 1]:
        for direction in [1, -1]:

            # --- Verification position fermee ---
            # A theta1_initial, la porte DOIT etre en position fermee
            theta1 = theta1_initial
            ax = Ax + L1 * np.cos(theta1)
            ay = Ay + L1 * np.sin(theta1)
            dx, dy = Bx - ax, By - ay
            d = np.sqrt(dx*dx + dy*dy)
            if d > Lc + L2 + 0.01 or d < abs(Lc - L2) - 0.01:
                continue

            # Trouver la position de b (intersection de 2 cercles)
            a_param = (Lc*Lc - L2*L2 + d*d) / (2*d)
            h = np.sqrt(max(0, Lc*Lc - a_param*a_param))
            mx = ax + a_param * dx / d
            my = ay + a_param * dy / d
            px, py = -dy / d * h, dx / d * h
            if branche == 0:
                bx, by = mx + px, my + py
            else:
                bx, by = mx - px, my - py

            # Calculer l'angle et la position de la porte
            angle_monde = np.arctan2(by - ay, bx - ax)
            angle_porte = angle_monde - ang_local
            co, si = np.cos(angle_porte), np.sin(angle_porte)
            tx = ax - (a_local[0]*co - a_local[1]*si)
            ty = ay - (a_local[0]*si + a_local[1]*co)

            # Verifier que c'est bien la position fermee: tx~0, ty~0, angle~0
            angle_mod = angle_porte % (2 * np.pi)
            if angle_mod > np.pi:
                angle_mod -= 2 * np.pi
            if (abs(tx) > 5 or abs(ty) > 5 or
                    (abs(angle_mod) > 0.1 and
                     abs(angle_mod - 2*np.pi) > 0.1 and
                     abs(angle_mod + 2*np.pi) > 0.1)):
                continue  # Ce n'est PAS la position fermee -> ignorer

            # --- Simulation du mouvement ---
            positions = []
            clearance_min = 1e6
            ok = True

            for i in range(N_STEPS):
                fraction = i / (N_STEPS - 1)  # 0.0 a 1.0
                theta1 = theta1_initial + direction * fraction * np.pi * sweep

                # Position du pivot 'a' sur le cercle de A
                ax = Ax + L1 * np.cos(theta1)
                ay = Ay + L1 * np.sin(theta1)

                # Trouver 'b' : intersection cercle(a, Lc) et cercle(B, L2)
                dx, dy = Bx - ax, By - ay
                d = np.sqrt(dx*dx + dy*dy)
                if d > Lc + L2 + 0.01 or d < abs(Lc - L2) - 0.01 or d < 1e-10:
                    ok = False
                    break

                a_param = (Lc*Lc - L2*L2 + d*d) / (2*d)
                h = np.sqrt(max(0, Lc*Lc - a_param*a_param))
                mx = ax + a_param * dx / d
                my = ay + a_param * dy / d
                px, py = -dy / d * h, dx / d * h
                if branche == 0:
                    bx, by = mx + px, my + py
                else:
                    bx, by = mx - px, my - py

                # Angle et position de la porte
                angle_monde = np.arctan2(by - ay, bx - ax)
                angle_porte = angle_monde - ang_local
                co, si = np.cos(angle_porte), np.sin(angle_porte)
                tx = ax - (a_local[0]*co - a_local[1]*si)
                ty = ay - (a_local[0]*si + a_local[1]*co)

                # Sauvegarder la position
                positions.append((tx, ty, angle_porte, ax, ay, bx, by))

                # Verifier les collisions (sauf step 0 = position fermee)
                if i > 0:
                    # 1. Porte vs murs
                    pts_monde = transformer(points, tx, ty, co, si)
                    cl = np.min(verifier_collisions(pts_monde))
                    clearance_min = min(clearance_min, cl)

                    # 2. Bras vs murs lateraux (pas la limite arriere)
                    # Les bras sont des tubes fins a Z=200 ou Z=1840, ils passent
                    # au-dessus/dessous du frigo derriere le mur.
                    # On verifie seulement: x > 0 (mur gauche) et x < OW si y < RWD (mur droit)
                    ARM_EXT = 20  # depassement tube au-dela des pivots
                    for (px_s, py_s, px_e, py_e) in [(Ax, Ay, ax, ay), (Bx, By, bx, by)]:
                        bdx = px_e - px_s; bdy = py_e - py_s
                        bl = np.sqrt(bdx*bdx + bdy*bdy)
                        if bl > 1:
                            bnx, bny = -bdy/bl, bdx/bl
                            hw = TUBE_BRAS_W / 2
                            ext = ARM_EXT / bl  # fraction de depassement
                            for t_frac in [-ext, 0.0, 0.25, 0.5, 0.75, 1.0, 1.0+ext]:
                                cx = px_s + t_frac * bdx
                                cy = py_s + t_frac * bdy
                                for side in [-hw, 0, hw]:
                                    bpx = cx + side * bnx
                                    bpy = cy + side * bny
                                    # Mur gauche: x > 0 si y < LWD
                                    if bpy < LWD:
                                        clearance_min = min(clearance_min, bpx)
                                    # Mur droit: x < OW si y < RWD
                                    if bpy < RWD:
                                        clearance_min = min(clearance_min, OW - bpx)
                                    # PAS de verif limite arriere pour les bras

                    # 3. Platine porte vs murs LATERAUX seulement
                    # La platine est fine (5mm tole), elle passe au-dessus du frigo
                    # comme les bras. Seule la porte (355mm) bloque l'espace arriere.
                    plat_pts_local = np.array([
                        [plat_x_min, DT], [plat_x_max, DT],
                        [plat_x_min, ay_door], [plat_x_max, ay_door],
                        [plat_x_min, by_door], [plat_x_max, by_door],
                        [ax_door, ay_door], [bx_door, by_door],
                    ])
                    plat_pts_monde = transformer(plat_pts_local, tx, ty, co, si)
                    plat_x = plat_pts_monde[:, 0]
                    plat_y = plat_pts_monde[:, 1]
                    # Mur gauche
                    mask_g = plat_y < LWD
                    if np.any(mask_g):
                        clearance_min = min(clearance_min, np.min(plat_x[mask_g]))
                    # Mur droit (retour dans l'ouverture)
                    mask_d = plat_y < RWD
                    if np.any(mask_d):
                        clearance_min = min(clearance_min, np.min(OW - plat_x[mask_d]))

            if not ok:
                continue

            # --- Verification position ouverte ---
            tx_final, ty_final, angle_final = positions[-1][:3]
            co, si = np.cos(angle_final), np.sin(angle_final)
            coins_ouverts = transformer(coins, tx_final, ty_final, co, si)
            x_max = np.max(coins_ouverts[:, 0])
            x_min = np.min(coins_ouverts[:, 0])

            # La porte doit etre derriere le mur droit (x > OW)
            if x_min < OW - 5:
                clearance_min = min(clearance_min, x_min - OW)
            # Et dans l'espace disponible (x < OW + EFF_BACK)
            if x_max > OW + EFF_BACK - 5:
                clearance_min = min(clearance_min, OW + EFF_BACK - x_max)
            # Et avoir tourne d'au moins 65 degres (objectif 75°)
            if abs(angle_final) < np.radians(65):
                clearance_min = min(clearance_min,
                                    -(75 - np.degrees(abs(angle_final))) * 2)

            if clearance_min > meilleur_resultat:
                meilleur_resultat = clearance_min
                meilleures_positions = positions

    return meilleur_resultat, meilleures_positions


def fonction_objectif(params):
    """Fonction a MINIMISER par l'optimiseur. Retourne -clearance."""
    cl, _ = simuler_mecanisme(*params)
    return -cl


# =============================================================================
# EXECUTION
# =============================================================================
if __name__ == '__main__':
    print("=" * 70)
    print("OPTIMISATION 4-BAR LINKAGE - PORTE EPAISSE")
    print("=" * 70)
    print()
    print("PARAMETRES FIXES:")
    print(f"  Ouverture        : {OW} mm")
    is_trapeze = TAPER_HINGE > 0 or TAPER_TRAILING > 0
    print(f"  Porte            : {DW} x {DT} mm (cadre {CADRE}mm)"
          f"{'  TRAPEZE' if is_trapeze else '  RECTANGLE'}")
    print(f"  Mur gauche       : {LWD} mm d'epaisseur")
    print(f"  Mur droit        : {RWD} mm d'epaisseur")
    print(f"  Espace derriere  : {SBR} mm + {EXTRA_BACK} mm = {EFF_BACK} mm")
    print(f"  Chanfrein        : aucun")
    # Cercle circonscrit: calculer le rayon du plus petit cercle contenant le trapeze
    coins = coins_porte()
    # Pour un quadrilatere convexe, le cercle circ. passe par les 2 coins les plus eloignes
    # On calcule toutes les distances entre coins
    dists = []
    for i in range(4):
        for j in range(i+1, 4):
            d = np.sqrt((coins[i,0]-coins[j,0])**2 + (coins[i,1]-coins[j,1])**2)
            dists.append((d, f"C{i+1}-C{j+1}"))
    dists.sort(reverse=True)
    print(f"  Forme porte      : {'TRAPEZE' if TAPER_HINGE>0 or TAPER_TRAILING>0 else 'RECTANGLE'}")
    if TAPER_HINGE > 0:
        print(f"    Taper charnieres (C2): {TAPER_HINGE}mm -> C2=({TAPER_HINGE},{DT})")
    if TAPER_TRAILING > 0:
        print(f"    Taper trailing  (C3): {TAPER_TRAILING}mm -> C3=({DW-TAPER_TRAILING},{DT})")
    print(f"  Distances entre coins:")
    for d, name in dists:
        print(f"    {name}: {d:.0f}mm {' (=cercle circ.)' if d==dists[0][0] else ''}")
    print(f"  Plus grande dist : {dists[0][1]} = {dists[0][0]:.0f}mm (exces vs ouverture: {dists[0][0]-OW:.0f}mm)")
    print()
    print(f"PARAMETRES A OPTIMISER ({len(BOUNDS)} variables):")
    print(f"  Ax     : [{BOUNDS[0][0]}, {BOUNDS[0][1]}] mm  (pivot A mur, x)")
    print(f"  Ay     : [{BOUNDS[1][0]}, {BOUNDS[1][1]}] mm  (pivot A mur, y)")
    print(f"  Bx     : [{BOUNDS[2][0]}, {BOUNDS[2][1]}] mm  (pivot B mur, x)")
    print(f"  By     : [{BOUNDS[3][0]}, {BOUNDS[3][1]}] mm  (pivot B mur, y)")
    print(f"  ax_door: [{BOUNDS[4][0]}, {BOUNDS[4][1]}] mm  (pivot a porte, x)")
    print(f"  bx_door: [{BOUNDS[5][0]}, {BOUNDS[5][1]}] mm  (pivot b porte, x)")
    print(f"  ay_door: [{BOUNDS[6][0]}, {BOUNDS[6][1]}] mm  (pivot a porte, y / profondeur)")
    print(f"  by_door: [{BOUNDS[7][0]}, {BOUNDS[7][1]}] mm  (pivot b porte, y / profondeur)")
    print(f"  sweep  : [{BOUNDS[8][0]}, {BOUNDS[8][1]}]     (fraction de pi, rotation bras 1)")
    print("N_STEPS:", N_STEPS)
    print()
    print("Lancement de l'optimisation (evolution differentielle)...")
    print("Cela peut prendre 2-3 minutes...")
    print()

    resultat = differential_evolution(
        fonction_objectif,
        BOUNDS,
        maxiter=300,
        popsize=60,
        tol=0.05,
        seed=42,
        mutation=(0.5, 1.5),
        recombination=0.9,
        disp=True,
    )

    clearance = -resultat.fun
    Ax, Ay, Bx, By, ax_d, bx_d, ay_d, by_d, sweep_opt = resultat.x
    L1 = np.sqrt((Ax - ax_d)**2 + (Ay - ay_d)**2)
    L2 = np.sqrt((Bx - bx_d)**2 + (By - by_d)**2)

    print()
    print("=" * 70)
    status = "OK" if clearance >= 5 else "SERRE" if clearance >= 0 else "COLLISION"
    print(f"RESULTAT: clearance = {clearance:.1f} mm [{status}]")
    print("=" * 70)
    print(f"  Pivot A (mur)          : ({Ax:.1f}, {Ay:.1f}) mm")
    print(f"  Pivot B (mur)          : ({Bx:.1f}, {By:.1f}) mm")
    print(f"  Pivot a (porte)        : ({ax_d:.1f}, {ay_d:.1f}) mm"
          f"{'  (patte ' + str(int(ay_d-DT)) + 'mm)' if ay_d > DT+1 else '  (sur face arriere)'}")
    print(f"  Pivot b (porte)        : ({bx_d:.1f}, {by_d:.1f}) mm"
          f"{'  (patte ' + str(int(by_d-DT)) + 'mm)' if by_d > DT+1 else '  (sur face arriere)'}")
    print(f"  Bras 1                 : {L1:.0f} mm")
    print(f"  Bras 2                 : {L2:.0f} mm")
    print(f"  Sweep                  : {sweep_opt:.2f} ({sweep_opt*180:.0f} degres de bras 1)")
    print()

    # Simulation detaillee pour affichage
    cl_detail, positions = simuler_mecanisme(*resultat.x)
    if positions:
        angle_final = np.degrees(positions[-1][2])
        print(f"  Rotation finale        : {angle_final:.1f} degres")
        print(f"  Clearance (detail)     : {cl_detail:.1f} mm")
