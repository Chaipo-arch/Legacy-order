# Legacy Order Report — Refactoring

## Contexte

Ce projet contient un générateur de rapports de commandes client. Le fichier d'origine (`order_report_legacy.py`) est un monolithe de 280+ lignes mélangeant parsing CSV, logique métier, calculs de remises et I/O dans une seule fonction `run()`.

L'objectif du refactoring est de rendre le code **lisible, testable et maintenable**, sans modifier le comportement observable — garanti par un test Golden Master.

---

## Golden Master

Avant tout refactoring, la sortie de `order_report_legacy.py` a été capturée dans `src/legacy/expected/report.txt`. Ce fichier sert de référence immuable pour tous les tests de non-régression.

```bash

# Lancer les tests
py -m pytest src/test/test_golden_master.py
```

---

## Lancer le projet

```bash
# Depuis la racine du projet
py -m src.refacto.order_report
```

Les imports relatifs (`from .loader import ...`) imposent d'exécuter le projet **comme module** depuis la racine, et non directement avec `py src/refacto/order_report.py`.

---

## Structure finale

```
src/
├── legacy/
│   ├── order_report_legacy.py   # Monolithe original — NE PAS MODIFIER
│   └── expected/
│       └── report.txt           # Golden Master
├── refacto/
│   ├── __init__.py
│   ├── models.py                # Dataclasses : Customer, Product, Order, Promotion, ShippingZone
│   ├── loader.py                # Parsing CSV → instances typées
│   ├── calculations.py          # Tax, shipping, handling, currency, loyalty points
│   ├── discounts.py             # Volume, weekend bonus, loyalty discount, cap
│   ├── io_handler.py            # Lecture fichiers, print, écriture JSON
│   └── order_report.py          # Orchestration pure
└── test/
    └── test_golden_master.py
```

---


## Règles préservées du legacy

Le legacy contient plusieurs règles implicites non documentées, toutes préservées :

| Règle | Localisation |
|---|---|
| Remise en cascade (chaque palier écrase le précédent) | `discounts.py` — `compute_volume_discount` |
| Bonus week-end : +5% sur la remise volume | `discounts.py` — `compute_weekend_bonus` |
| Plafond remise global à 200€, ajustement proportionnel | `discounts.py` — `cap_and_adjust_discounts` |
| Bonus matin : -3% si commande avant 10h | `calculations.py` — `apply_promotion_and_morning` |
| Remise FIXED appliquée par ligne (bug intentionnel conservé) | `calculations.py` — `apply_promotion_and_morning` |
| Taxe par ligne si au moins un produit non taxable | `calculations.py` — `compute_tax` |
| Majoration x1.2 pour ZONE3 et ZONE4 | `calculations.py` — `compute_shipping` |
| Frais de manutention doublés au-delà de 20 articles | `calculations.py` — `compute_handling` |
| Tri des clients par ID avant génération du rapport | `order_report.py` — `compute_report` |

---

## Qualité du code et tests

Faute de temps, les tests unitaires supplémentaires (hors Golden Master) n’ont pas été implémentés.

De même, la correction de la qualité du code via le linter n’a pas été finalisée.
L’analyse Pylint donne actuellement une note de 8.33/10, indiquant un code globalement propre mais perfectible sur certains aspects de style et de structure.

