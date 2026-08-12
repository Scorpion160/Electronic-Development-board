# EmbedLab Board Tester

Outil de diagnostic guidé pour vérifier les modules de l'EmbedLab Board sans écrire de code pendant les TP.

## Objectif

L'application Windows guide l'utilisateur pour :

1. choisir le microcontrôleur ;
2. choisir le port série ;
3. sélectionner un test rapide, complet ou ciblé ;
4. consulter le plan de câblage adapté au microcontrôleur ;
5. téléverser le firmware agent de test ;
6. piloter les tests par liaison série ;
7. enregistrer un rapport de diagnostic.

## Version actuelle

Cette base met en place :

- une interface Python simple et portable avec `tkinter` ;
- la détection des ports série via `pyserial` ;
- des profils JSON pour Arduino Uno, Nano, Mega, ESP32, STM32 et PIC16F ;
- un fichier `pin_mappings.json` qui propose les broches selon le microcontrôleur choisi ;
- un plan de tests modulaire couvrant les entrées, sorties, capteurs, affichages, bus et étages de puissance ;
- un firmware agent Arduino pour Uno/Nano/Mega ;
- la génération d'un rapport CSV.

Le téléversement automatique complet est prévu d'abord pour Arduino Uno/Nano/Mega via `arduino-cli`. Pour ESP32, STM32 et PIC16F, les profils et le mode guidé sont préparés, mais le support de flash automatique sera ajouté progressivement selon les cartes et programmateurs réellement utilisés au laboratoire.

## Principe du mapping de broches

Chaque microcontrôleur possède un profil dans :

```text
profiles/boards.json
```

et un plan de câblage dans :

```text
profiles/pin_mappings.json
```

L'application découpe automatiquement le test complet en étapes. Par exemple, avec Arduino Uno/Nano, le test complet est divisé en plusieurs câblages, car les broches sont limitées. Avec Arduino Mega, plusieurs modules peuvent être testés avec moins de changements de câblage.

## Installation développeur

```powershell
cd tools\embedlab_tester
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app\main.py
```

## Compilation en exécutable Windows

```powershell
cd tools\embedlab_tester
.\build_windows.ps1
```

Le fichier généré sera placé dans :

```text
dist\EmbedLab_Board_Tester.exe
```

## Téléversement du firmware agent

Le bouton **Téléverser firmware agent** utilise `arduino-cli`. Avant de lancer l'application, vérifier dans PowerShell :

```powershell
arduino-cli version
arduino-cli core list
```

Si le cœur Arduino AVR n'est pas installé :

```powershell
arduino-cli core update-index
arduino-cli core install arduino:avr
```

Si rien ne semblait se passer dans l'ancienne interface, la nouvelle version affiche maintenant :

- un statut visible dans le panneau de gauche ;
- un message si `arduino-cli` est introuvable ;
- un journal de compilation/téléversement visible en bas à droite ;
- une fenêtre d'erreur si la compilation ou l'upload échoue.

Après téléversement, cliquer sur **Connecter / PING**. La réponse attendue avec l'agent actuel est :

```text
EMBEDLAB_AGENT 1.1
```

## Commandes série du firmware agent

L'application envoie d'abord un petit firmware agent dans le microcontrôleur. Ensuite, elle communique avec lui par port série. Le microcontrôleur exécute les commandes reçues : allumer une LED, lire un bouton, lire une entrée analogique, générer un son, piloter le registre 74HC595N, lancer un test LCD 4 bits ou faire une marche sur plusieurs sorties.

Commandes de base :

```text
PING
PINMODE 5 OUTPUT
DWRITE 5 1
DREAD 12
AREAD A0
PWM 11 128
TONE A3 440 500
I2C_SCAN
```

Commandes avancées ajoutées dans l'agent 1.1 :

```text
SHIFT595 5 6 7 0xAA
WALK 250 2 3 4 5 6 7 8 9
LCD4_TEST 2 3 4 5 6 7
PCF8574_WRITE 0x20 0x55
PCF8574_WALK 0x20 200
RESET_OUTPUTS
```

Ces commandes permettent de commencer l'automatisation des tests pour le 74HC595N, le LCD 1602, le PCF8574N, l'afficheur 7 segments et la matrice LED 8x8. Certains tests restent visuels : l'application lance la séquence et l'utilisateur confirme si l'affichage, le son ou la commutation est correct.

## Rappel sécurité

- Toujours placer J10 sur la bonne tension logique : 5 V pour Arduino Uno/Nano/Mega, 3,3 V pour ESP32/STM32/Pico/FPGA.
- Toujours relier le GND du microcontrôleur au GND de l'EmbedLab Board.
- Ne jamais alimenter un moteur ou un servo depuis le 7805 de la carte.
- Utiliser une alimentation externe pour les charges de puissance, puis commander la charge via relais, MOSFET ou pont en H.
