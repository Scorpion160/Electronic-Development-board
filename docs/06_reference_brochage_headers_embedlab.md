# Référence de brochage des headers EmbedLab Board

Cette page reprend les signaux visibles sur la vue rapprochée des connecteurs d'accès aux signaux. Elle sert de base au logiciel **EmbedLab Board Tester** pour guider les câblages de diagnostic.

> Important : la broche de commande du MOSFET n'apparaît pas sur cette vue rapprochée. Elle doit être confirmée depuis le schéma EasyEDA ou le routage complet avant d'être ajoutée définitivement au mapping automatique.

## Header gauche

### Rangée supérieure

| Position | Signal |
|---:|---|
| 1 | Switch1 |
| 2 | Switch2 |
| 3 | Switch3 |
| 4 | Switch4 |
| 5 | Switch5 |
| 6 | Switch6 |
| 7 | LM35 |
| 8 | LDR |
| 9 | POT1 |
| 10 | POT2 |
| 11 | Buzzer |
| 12 | LED1 |
| 13 | LED2 |
| 14 | LED3 |
| 15 | LED4 |
| 16 | LED5 |
| 17 | LED6 |
| 18 | LED7 |
| 19 | LED8 |
| 20 | LED9 |
| 21 | LED10 |

### Rangée inférieure

| Position | Signal |
|---:|---|
| 1 | BP1 |
| 2 | BP2 |
| 3 | BP3 |
| 4 | BP4 |
| 5 | BP5 |
| 6 | Matrix_C8 |
| 7 | Matrix_C7 |
| 8 | Matrix_C6 |
| 9 | Matrix_C5 |
| 10 | Matrix_C4 |
| 11 | Matrix_C3 |
| 12 | Matrix_C2 |
| 13 | Matrix_C1 |
| 14 | Matrix_R1 |
| 15 | Matrix_R2 |
| 16 | Matrix_R3 |
| 17 | Matrix_R4 |
| 18 | Matrix_R5 |
| 19 | Matrix_R6 |
| 20 | Matrix_R7 |
| 21 | Matrix_R8 |

## Header droit

### Rangée supérieure

| Position | Signal |
|---:|---|
| 1 | RGB1_R |
| 2 | RGB1_G |
| 3 | RGB1_B |
| 4 | RGB2_R |
| 5 | RGB2_G |
| 6 | RGB2_B |
| 7 | RGB3_R |
| 8 | RGB3_G |
| 9 | RGB3_B |
| 10 | LCD_RS |
| 11 | LCD_E |
| 12 | LCD_D4 |
| 13 | LCD_D5 |
| 14 | LCD_D6 |
| 15 | LCD_D7 |
| 16 | PONT_H1 |
| 17 | PONT_H2 |
| 18 | PONT_H3 |
| 19 | PONT_H4 |

### Rangée inférieure

| Position | Signal |
|---:|---|
| 1 | DP |
| 2 | SEG_G |
| 3 | SEG_F |
| 4 | SEG_E |
| 5 | SEG_D |
| 6 | SEG_C |
| 7 | SEG_B |
| 8 | SEG_A |
| 9 | DIGIT4 |
| 10 | DIGIT3 |
| 11 | DIGIT2 |
| 12 | DIGIT1 |
| 13 | GND |
| 14 | GND |
| 15 | +5V |
| 16 | +5V |
| 17 | +3V3 |
| 18 | +3V3 |
| 19 | Relais |

## Points à confirmer

| Signal | Statut | Action |
|---|---|---|
| Commande MOSFET | Non visible sur la vue rapprochée | Confirmer le nom du pad/header depuis le schéma ou le PCB complet. |
| PONT_H1 à PONT_H4 | Visible | Définir dans le logiciel si le test utilise 2 ou 4 entrées selon le câblage final du pont en H. |
| LED1 à LED10 | Visible | Associer LED1..LED9 au chenillard et LED10 au test PWM. |
| Matrix_R/C | Visible | Utiliser ces noms pour générer les écrans de câblage de la matrice 8x8. |
