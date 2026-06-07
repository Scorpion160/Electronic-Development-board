# EmbedLab Board - V1.0

Carte de developpement pedagogique pour travaux pratiques en systemes embarques, electronique, informatique industrielle et prototypage.

## Depot officiel

https://github.com/Scorpion160/Electronic-Development-board

## Contenu du depot

- `docs/` : manuel d'utilisation complet, fiche de prise en main rapide et sources LaTeX.
- `figures/` : vue 3D annotee, photo principale de la carte, image de routage et autres figures.
- `hardware/easyeda/` : fichiers EasyEDA SCH/PCB.
- `hardware/gerber/` : Gerber et export 3D/OBJ.
- `hardware/bom/` : BOM EasyEDA et liste vendeur simplifiee.
- `hardware/pnp/` : fichier Pick and Place.
- `qr/` : QR code pointant vers le depot GitHub.

## Documents principaux

- Manuel complet : `docs/manuel_embedlab_board.pdf`
- Fiche rapide : `docs/fiche_datasheet_embedlab.pdf`
- Liste vendeur : `hardware/bom/liste_composants_embedlab_5_cartes.xlsx`

## Rappels importants

- Toujours verifier la position du cavalier `J10` avant de lire un capteur analogique.
- Utiliser `J10 = 5 V` pour Arduino 5 V et `J10 = 3,3 V` pour ESP32, STM32, FPGA ou Pico.
- Ne pas alimenter moteurs ou servos depuis le regulateur `LM7805`.
- Utiliser le relais, le MOSFET et le pont en H uniquement avec des charges basse tension dans le cadre des TP.
- Le haut-parleur a ete retire de cette version ; seul le buzzer reste present.
