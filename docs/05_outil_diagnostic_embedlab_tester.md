# Outil de diagnostic EmbedLab Board Tester

## Objectif

L'objectif est de fournir au professeur, au technicien de laboratoire et aux étudiants un outil simple pour tester l'EmbedLab Board sans devoir écrire un nouveau programme à chaque manipulation.

L'utilisateur doit pouvoir :

1. lancer une application Windows ;
2. choisir le microcontrôleur utilisé ;
3. choisir le port COM ;
4. sélectionner un test rapide, complet ou ciblé ;
5. suivre les consignes de câblage ;
6. téléverser le firmware agent de test ;
7. exécuter le protocole de test ;
8. enregistrer un rapport de diagnostic.

## Architecture retenue

```text
PC Windows / Application Python
        ↓ USB série
Microcontrôleur de test
        ↓ signaux GPIO / ADC / PWM / I2C / UART
EmbedLab Board
```

Le microcontrôleur joue le rôle d'agent de test. Il reçoit des commandes depuis l'application Python, exécute l'action demandée puis renvoie une réponse.

## Modules couverts par les définitions de test

- LEDs rouges ;
- LEDs RGB ;
- boutons poussoirs ;
- DIP-switch ;
- potentiomètres ;
- LDR ;
- LM35 ;
- buzzer ;
- interface USB-série CH340G ;
- bus I2C / PCF8574N ;
- relais ;
- MOSFET ;
- pont en H.

## Microcontrôleurs prévus

| Microcontrôleur | État actuel | Remarque |
|---|---|---|
| Arduino Uno | MVP supporté | Téléversement via arduino-cli |
| Arduino Nano | MVP supporté | Téléversement via arduino-cli, attention bootloader |
| Arduino Mega | MVP supporté | Le plus pratique pour tester beaucoup de broches |
| ESP32 | Profil préparé | J10 sur 3,3 V ; téléversement à finaliser |
| STM32 | Profil préparé | Méthode de flash dépend de la carte |
| PIC16F | Profil préparé | Prévoir HEX + programmateur PICkit/MPLAB IPE |

## Règles de sécurité intégrées

- Rappeler la position de J10 selon la tension logique.
- Imposer le GND commun avant les mesures.
- Séparer logique et puissance.
- Guider les tests de puissance avec charge DC basse tension uniquement.

## Prochaines améliorations

1. Ajouter un écran de correspondance automatique entre broches du microcontrôleur et headers EmbedLab.
2. Ajouter des images de câblage par module.
3. Ajouter un mode test complet découpé automatiquement selon le nombre de broches disponibles.
4. Ajouter la génération de rapport PDF en plus du CSV.
5. Ajouter le support de flash ESP32, STM32 et PIC16F.
6. Ajouter des tests spécialisés LCD, matrice LED 8x8, afficheur 7 segments, 74HC595N et SN74AHCT125.
