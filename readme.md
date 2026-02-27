# Legacy Order Report — Refactoring

## Installation

### Prérequis
- Python 3.10+
- pip

### Commandes

```bash
# Cloner le projet et se placer à la racine
cd legacy-order

# Créer et activer l'environnement virtuel
python -m venv venv

# Windows
venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

---

## Exécution

### Exécuter le code refactoré

```bash
# Depuis la racine du projet
py -m src.refacto.order_report
```

---

### Exécuter les tests

```bash
pytest
```

---
## Choix de Refactoring

### Problèmes Identifiés dans le Legacy

1. **God Function** : la fonction `run()` fait 280+ lignes et mélange parsing CSV, logique métier, calculs de remises et I/O dans un seul bloc séquentiel.
   - Impact : impossible à tester unitairement, impossible à modifier sans tout relire.

2. **Parsing incohérent** : trois styles de parsing différents dans la même fonction (`csv.reader`, `readlines()` + split manuel, `csv.DictReader`).
   - Impact : comportements subtils différents selon l'entité, bugs silencieux en cas de fichier malformé.

3. **Dictionnaires anonymes** : toutes les entités (`Customer`, `Product`, `Order`...) sont des `dict` sans structure garantie.
   - Impact : accès fragiles avec `.get('key', default)`, aucune autocomplétion, les erreurs de nommage passent silencieusement.

4. **Magic numbers** : valeurs hardcodées dispersées (`0.05`, `0.10`, `0.15`, `0.20`, `10`, `5`, `0.3`, `0.25`, `1.2`...).
   - Impact : impossible de comprendre leur signification sans contexte, risque élevé d'incohérence en cas de modification.

5. **Règles métier cachées** : bonus matin (-3% avant 10h), bonus week-end (+5% sur remise), majoration ZONE3/ZONE4, plafond remise à 200€ — aucune de ces règles n'est documentée ni nommée.
   - Impact : un développeur qui lit le code ne peut pas deviner l'intention métier derrière les conditions.

6. **Effets de bord mélangés** : `print()` et écriture JSON surprises au milieu de la logique de calcul.
   - Impact : non testable sans capturer stdout, effets invisibles lors de l'appel de `run()`.

---

### Solutions Apportées

1. **Extraction du parsing** dans `loader.py` — une fonction par entité, style unique (`csv.DictReader` ou `csv.reader`), silencieux sur les lignes malformées comme le legacy.
   - Justification : responsabilité unique, parsing séparé de la logique métier.

2. **Modèles typés** dans `models.py` — `dataclasses` Python pour `Customer`, `Product`, `Order`, `Promotion`, `ShippingZone`.
   - Justification : pas de dépendance externe (vs `pydantic`), accès par attribut, valeurs par défaut déclaratives, les `None` remplacent les dict vides et rendent les cas manquants explicites.

3. **Extraction des remises** dans `discounts.py` — les 4 fonctions de remise sont isolées avec des noms explicites.
   - Justification : les règles de remise sont les plus susceptibles de changer ; les isoler facilite les tests unitaires et la lecture.

4. **Isolation des I/O** dans `io_handler.py` — `read_data()`, `write_report()`, `write_json()`.
   - Justification : `compute_report()` dans `order_report.py` devient une fonction pure, testable par injection directe sans fichiers CSV.

5. **Constantes nommées** — remplacement de tous les magic numbers par des constantes en majuscules (`TAX`, `SHIPPING_LIMIT`, `MAX_DISCOUNT`, `LOYALTY_RATIO`, `handling_fee`).
   - Justification : la signification métier est immédiatement lisible.

---

### Architecture Choisie

```
src/
├── legacy/
│   ├── order_report_legacy.py   # Monolithe original — NE PAS MODIFIER
│   └── expected/
│       └── report.txt           # Golden Master capturé
├── refacto/
│   ├── __init__.py
│   ├── models.py                # Dataclasses : entités typées
│   ├── loader.py                # Parsing CSV → instances typées
│   ├── calculations.py          # Tax, shipping, handling, currency, loyalty points
│   ├── discounts.py             # Volume, weekend bonus, loyalty discount, cap
│   ├── io_handler.py            # Lecture fichiers, print, écriture JSON
│   └── order_report.py          # Orchestration pure (compute_report + run)
└── test/
    └── test_golden_master.py
```
---

## Limites et Améliorations Futures

### Ce qui n'a pas été fait (par manque de temps)

-  **Score Pylint à 10/10** — score actuel : **8.33/10**. 
-  **Tests unitaires** sur les fonctions pures (`compute_volume_discount`, `compute_tax`, `compute_shipping`, etc.)
-  **Tests d'intégration** avec des jeux de données synthétiques (client sans commande, produit introuvable, promo expirée)
-  **Formatage du rapport** extrait dans un module dédié `formatter.py` — `compute_report()` mélange encore calculs et construction des lignes de texte

### Pistes d'Amélioration Future
- Atteindre 10/10 Pylint en renommant les variables courtes et en nettoyant les `else` redondants
- Paramétrer les constantes (`TAX`, `MAX_DISCOUNT`) via un fichier de configuration ou des variables d'environnement
- Rédigez des test