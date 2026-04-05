# Porte-etagere cuisine-buanderie

Conception d'une porte epaisse avec etageres integrees entre la cuisine et la buanderie,
montee sur un mecanisme 4-bar linkage (bras articules).

## Le probleme

L'ouverture fait 870mm de large. La porte fait 355mm d'epaisseur (pour les etageres).
La diagonale de la porte (940mm) depasse l'ouverture de 70mm, ce qui empeche un pivot
classique de fonctionner : le coin de la porte heurte le mur en pivotant.

## La solution

Un mecanisme a **4 barres articulees** (4-bar linkage) avec :
- 2 bras rigides reliant le mur droit (cote charnieres) a la porte
- 2 pattes qui sortent de la face arriere (buanderie) de la porte
- Le mecanisme combine translation + rotation, evitant la collision diagonale

La porte est **trapezoidale** (plus etroite cote buanderie) et encadree par des
**cadres de 25mm** de chaque cote, ce qui reduit les dimensions effectives.

## Dimensions cles

| Element | Valeur |
|---|---|
| Ouverture | 870mm |
| Mur gauche (trailing) | 355mm d'epaisseur |
| Mur droit (charnieres) | 425mm d'epaisseur |
| Espace derriere mur droit | 380mm (frigo juste derriere) |
| Marche cuisine-buanderie | 190mm |
| Hauteur porte | ~2040mm |

## Solution retenue

| Parametre | Valeur |
|---|---|
| Porte (cote cuisine) | 820 x 355mm |
| Forme | Trapeze, taper 60mm chaque coin buanderie |
| Face buanderie (etageres) | 700mm |
| Cadres | 25mm chaque cote (symetrique) |
| Pivot A (mur) | x=1238, y=428 |
| Pivot B (mur) | x=1188, y=532 |
| Patte a | 95mm, a x=563 sur la porte |
| Patte b | 188mm, a x=743 sur la porte |
| Bras 1 | 675mm |
| Bras 2 | 446mm |
| Rotation | ~91 degres |
| Clearance | ~14-24mm (selon resolution de simulation) |

## Structure du projet

```
porte-buanderie/
  calculs/
    optimisation_documentee.py  # Script principal: parametres + optimiseur
    animate_resultat.py         # Generation d'animation GIF (matplotlib)
    requirements.txt            # numpy, scipy, matplotlib, svgwrite, Pillow
  dessins/
    generate_plans.py           # Generation de plans SVG cotes
  freecad/
    porte_animable.py           # Genere un FCStd avec 21 positions
    live_animation.py           # Animation live via socket FreeCAD (WIP)
  exports/
    RESULTAT_animation.gif      # Animation du mecanisme
    plan_vue_dessus.svg         # Plan cote (vue de dessus)
    plan_porte_detail.svg       # Detail porte + etageres
    porte_animable.FCStd        # Modele 3D FreeCAD (21 positions groupees)
    frames_resultat/            # Frames PNG de l'animation
```

## Lancer l'optimisation

```bash
cd porte-buanderie
python3 -m venv .venv && source .venv/bin/activate
pip install -r calculs/requirements.txt
python3 calculs/optimisation_documentee.py
```

Modifier les parametres en haut de `optimisation_documentee.py` puis relancer.

## Generer l'animation GIF

Apres optimisation, mettre a jour les parametres dans `animate_resultat.py` puis :
```bash
python3 calculs/animate_resultat.py
# -> exports/RESULTAT_animation.gif
```

## Systeme de coordonnees

Vue de dessus, oriente comme depuis la cuisine :
- **X** : gauche (0) a droite (870)
- **Y** : cuisine (0) vers buanderie (positif)
- Mur gauche = cote trailing (x < 0), 355mm d'epaisseur
- Mur droit = cote charnieres (x > 870), 425mm d'epaisseur

## Prochaines etapes

- [ ] Valider les mesures sur place
- [ ] Animation FreeCAD live (socket server crash a resoudre)
- [ ] Plans techniques detailles des charnieres
- [ ] Choix materiaux (porte, bras, axes, roulements)
- [ ] Conception des roulettes (arc au sol buanderie)
- [ ] Prototype carton echelle 1:1
- [ ] Construction
