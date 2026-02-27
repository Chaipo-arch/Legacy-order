import json
import os

from .loader import (
    load_customers,
    load_products,
    load_shipping_zones,
    load_promotions,
    load_orders,
)


def read_data(data_dir):
    """Charge les 5 datasets depuis le dossier data. Aucune logique métier."""
    return (
        load_customers(os.path.join(data_dir, 'customers.csv')),
        load_products(os.path.join(data_dir, 'products.csv')),
        load_shipping_zones(os.path.join(data_dir, 'shipping_zones.csv')),
        load_promotions(os.path.join(data_dir, 'promotions.csv')),
        load_orders(os.path.join(data_dir, 'orders.csv')),
    )


def write_report(result):
    """Affiche le rapport en console."""
    print(result)


def write_json(json_data, output_path):
    """Écrit l'export JSON sur disque."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)