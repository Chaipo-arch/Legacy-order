# src/test/test_golden_master.py

import os
import sys
import json
import pytest

# Ajouter src au path pour que Python trouve legacy/refacto/loader
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # src
sys.path.insert(0, base_dir)

from legacy.order_report_legacy import run as legacy_run
from refacto.order_report import run as refactored_run

@pytest.fixture
def golden_master_path():
    return os.path.join(base_dir, "legacy", "expected", "report.txt")

@pytest.fixture
def json_output_path():
    return os.path.join(base_dir, "legacy", "output.json")

def test_golden_master(golden_master_path, json_output_path):
    # Exécution legacy
    legacy_output = legacy_run()

    # Lecture Golden Master
    with open(golden_master_path, "r", encoding="utf-8") as f:
        expected_output = f.read()

    # Comparaison texte printé
    assert legacy_output == expected_output, "Le legacy ne correspond plus au Golden Master !"

    # Exécution refactoré
    refactored_output = refactored_run()
    assert refactored_output == expected_output, "Le refactor modifie le comportement !"

    # Vérification du JSON généré
    with open(json_output_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    # Vérifier que tous les clients du texte existent dans le JSON
    customer_ids_in_output = [
        line.split("(")[-1].split(")")[0]
        for line in expected_output.splitlines()
        if line.startswith("Customer:")
    ]
    json_customer_ids = [c["customer_id"] for c in json_data]

    assert sorted(customer_ids_in_output) == sorted(json_customer_ids), \
        "Le JSON ne correspond pas aux clients du rapport !"