"""
Legacy Order Report Generator
DO NOT USE IN PRODUCTION
"""

import csv
import os
import json
import math
from datetime import datetime


TAX = 0.2
SHIPPING_LIMIT = 50
SHIP = 5.0
premium_threshold = 1000
LOYALTY_RATIO = 0.01
handling_fee = 2.5
MAX_DISCOUNT = 200

def run():
    """Fonction principale qui fait TOUT (280+ lignes)"""
    base = os.path.dirname(__file__)
    cust_path = os.path.join(base, 'data', 'customers.csv')
    ord_path = os.path.join(base, 'data', 'orders.csv')
    prod_path = os.path.join(base, 'data', 'products.csv')
    ship_path = os.path.join(base, 'data', 'shipping_zones.csv')
    promo_path = os.path.join(base, 'data', 'promotions.csv')

    # Lecture customers (parsing mélangé avec logique)
    customers = {}
    with open(cust_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            customers[row[0]] = {
                'id': row[0],
                'name': row[1],
                'level': row[2] if len(row) > 2 else 'BASIC',
                'shipping_zone': row[3] if len(row) > 3 else 'ZONE1',
                'currency': row[4] if len(row) > 4 else 'EUR'
            }

    # Lecture products (duplication du parsing, méthode différente)
    products = {}
    f = open(prod_path, 'r', encoding='utf-8')
    lines = f.readlines()
    f.close()
    for i in range(1, len(lines)):  # skip header
        try:
            parts = lines[i].strip().split(',')
            products[parts[0]] = {
                'id': parts[0],
                'name': parts[1],
                'category': parts[2],
                'price': float(parts[3]),
                'weight': float(parts[4]) if len(parts) > 4 else 1.0,
                'taxable': parts[5].lower() == 'true' if len(parts) > 5 else True
            }
        except:
            # Skip silencieux
            pass

    # Lecture shipping zones (encore une autre variation avec DictReader)
    shipping_zones = {}
    with open(ship_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            shipping_zones[row['zone']] = {
                'zone': row['zone'],
                'base': float(row['base']),
                'per_kg': float(row.get('per_kg', 0.5))
            }

    # Lecture promotions (parsing manuel avec split)
    promotions = {}
    if os.path.exists(promo_path):
        try:
            with open(promo_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if i == 0 or not line.strip():
                        continue
                    p = line.split(',')
                    promotions[p[0]] = {
                        'code': p[0],
                        'type': p[1],
                        'value': p[2],
                        'active': p[3] != 'false' if len(p) > 3 else True
                    }
        except Exception as e:
            # Ignore les erreurs de fichier promo
            pass

    # Lecture orders (mélange DictReader et validation)
    orders = []
    with open(ord_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                qty = int(row['qty'])
                price = float(row['unit_price'])
                
                if qty <= 0 or price < 0:
                    continue  # validation silencieuse
                
                orders.append({
                    'id': row['id'],
                    'customer_id': row['customer_id'],
                    'product_id': row['product_id'],
                    'qty': qty,
                    'unit_price': price,
                    'date': row.get('date', ''),
                    'promo_code': row.get('promo_code', ''),
                    'time': row.get('time', '12:00')
                })
            except Exception as e:
                # Skip silencieux
                continue

    # Calcul points de fidélité (première duplication)
    loyalty_points = {}
    for o in orders:
        cid = o['customer_id']
        if cid not in loyalty_points:
            loyalty_points[cid] = 0
        # Calcul basé sur prix commande
        loyalty_points[cid] += o['qty'] * o['unit_price'] * LOYALTY_RATIO

    # Groupement par client (logique métier mélangée avec aggregation)
    totals_by_customer = {}
    for o in orders:
        cid = o['customer_id']
        
        # Récupération produit avec fallback
        prod = products.get(o['product_id'], {})
        base_price = prod.get('price', o['unit_price'])
        
        # Application promo (logique complexe et bugguée)
        promo_code = o['promo_code']
        discount_rate = 0
        fixed_discount = 0
        
        if promo_code and promo_code in promotions:
            promo = promotions[promo_code]
            if promo['active']:
                if promo['type'] == 'PERCENTAGE':
                    discount_rate = float(promo['value']) / 100
                elif promo['type'] == 'FIXED':
                    # Bug: appliqué par ligne au lieu de global
                    fixed_discount = float(promo['value'])
        
        # Calcul ligne avec réduction promo
        line_total = o['qty'] * base_price * (1 - discount_rate) - fixed_discount * o['qty']
        
        # Bonus matin (règle cachée basée sur heure)
        hour = int(o['time'].split(':')[0])
        morning_bonus = 0
        if hour < 10:
            morning_bonus = line_total * 0.03  # 3% réduction supplémentaire
        line_total = line_total - morning_bonus
        
        if cid not in totals_by_customer:
            totals_by_customer[cid] = {
                'subtotal': 0.0,
                'items': [],
                'weight': 0.0,
                'promo_discount': 0.0,
                'morning_bonus': 0.0
            }
        
        totals_by_customer[cid]['subtotal'] += line_total
        totals_by_customer[cid]['weight'] += prod.get('weight', 1.0) * o['qty']
        totals_by_customer[cid]['items'].append(o)
        totals_by_customer[cid]['morning_bonus'] += morning_bonus

    # Génération rapport (mélange calculs + formatage + I/O)
    output_lines = []
    json_data = []
    grand_total = 0.0
    total_tax_collected = 0.0

    # Tri par ID client (comportement à préserver)
    sorted_customer_ids = sorted(totals_by_customer.keys())

    for cid in sorted_customer_ids:
        cust = customers.get(cid, {})
        name = cust.get('name', 'Unknown')
        level = cust.get('level', 'BASIC')
        zone = cust.get('shipping_zone', 'ZONE1')
        currency = cust.get('currency', 'EUR')

        sub = totals_by_customer[cid]['subtotal']

        # Remise par paliers (duplication + magic numbers)
        disc = 0.0
        if sub > 50:
            disc = sub * 0.05
        if sub > 100:
            disc = sub * 0.10  # écrase la précédente (bug intentionnel)
        if sub > 500:
            disc = sub * 0.15
        if sub > 1000 and level == 'PREMIUM':
            disc = sub * 0.20
        
        # Bonus weekend (règle cachée basée sur date)
        first_order_date = totals_by_customer[cid]['items'][0].get('date', '') if totals_by_customer[cid]['items'] else ''
        day_of_week = 0
        if first_order_date:
            try:
                dt = datetime.strptime(first_order_date, '%Y-%m-%d')
                day_of_week = dt.weekday()
            except:
                pass
        # weekday: 0=Monday, 5=Saturday, 6=Sunday
        if day_of_week == 5 or day_of_week == 6:
            disc = disc * 1.05  # 5% bonus sur remise

        # Calcul remise fidélité (duplication)
        loyalty_discount = 0.0
        pts = loyalty_points.get(cid, 0)
        if pts > 100:
            loyalty_discount = min(pts * 0.1, 50.0)
        if pts > 500:
            loyalty_discount = min(pts * 0.15, 100.0)  # écrase précédent

        # Plafond remise global (règle cachée)
        total_discount = disc + loyalty_discount
        if total_discount > MAX_DISCOUNT:
            total_discount = MAX_DISCOUNT
            # Ajustement proportionnel (logique complexe)
            ratio = MAX_DISCOUNT / (disc + loyalty_discount) if (disc + loyalty_discount) > 0 else 1
            disc = disc * ratio
            loyalty_discount = loyalty_discount * ratio

        # Calcul taxe (gestion spéciale par produit)
        taxable = sub - total_discount
        tax = 0.0
        
        # Vérifier si tous produits taxables
        all_taxable = True
        for item in totals_by_customer[cid]['items']:
            prod = products.get(item['product_id'])
            if prod and prod.get('taxable', True) == False:
                all_taxable = False
                break
        
        if all_taxable:
            tax = round(taxable * TAX, 2)  # Arrondi 2 décimales
        else:
            # Calcul taxe par ligne (plus complexe)
            for item in totals_by_customer[cid]['items']:
                prod = products.get(item['product_id'])
                if prod and prod.get('taxable', True) != False:
                    item_total = item['qty'] * prod.get('price', item['unit_price'])
                    tax += item_total * TAX
            tax = round(tax, 2)

        # Frais de port complexes (duplication)
        ship = 0.0
        weight = totals_by_customer[cid]['weight']
        
        if sub < SHIPPING_LIMIT:
            ship_zone = shipping_zones.get(zone, {'base': 5.0, 'per_kg': 0.5})
            base_ship = ship_zone['base']
            
            if weight > 10:
                ship = base_ship + (weight - 10) * ship_zone['per_kg']
            elif weight > 5:
                # Palier intermédiaire (règle cachée)
                ship = base_ship + (weight - 5) * 0.3
            else:
                ship = base_ship
            
            # Majoration zones éloignées
            if zone == 'ZONE3' or zone == 'ZONE4':
                ship = ship * 1.2
        else:
            # Livraison gratuite mais frais manutention poids élevé
            if weight > 20:
                ship = (weight - 20) * 0.25

        # Frais de gestion (magic number + condition cachée)
        handling = 0.0
        item_count = len(totals_by_customer[cid]['items'])
        if item_count > 10:
            handling = handling_fee
        if item_count > 20:
            handling = handling_fee * 2  # double pour grosses commandes

        # Conversion devise (règle cachée pour non-EUR)
        currency_rate = 1.0
        if currency == 'USD':
            currency_rate = 1.1
        elif currency == 'GBP':
            currency_rate = 0.85

        total = round((taxable + tax + ship + handling) * currency_rate, 2)
        grand_total += total
        total_tax_collected += tax * currency_rate

        # Formatage texte (dispersé, pas de fonction dédiée)
        output_lines.append(f'Customer: {name} ({cid})')
        output_lines.append(f'Level: {level} | Zone: {zone} | Currency: {currency}')
        output_lines.append(f'Subtotal: {sub:.2f}')
        output_lines.append(f'Discount: {total_discount:.2f}')
        output_lines.append(f'  - Volume discount: {disc:.2f}')
        output_lines.append(f'  - Loyalty discount: {loyalty_discount:.2f}')
        if totals_by_customer[cid]['morning_bonus'] > 0:
            output_lines.append(f"  - Morning bonus: {totals_by_customer[cid]['morning_bonus']:.2f}")
        output_lines.append(f'Tax: {tax * currency_rate:.2f}')
        output_lines.append(f'Shipping ({zone}, {weight:.1f}kg): {ship:.2f}')
        if handling > 0:
            output_lines.append(f'Handling ({item_count} items): {handling:.2f}')
        output_lines.append(f'Total: {total:.2f} {currency}')
        output_lines.append(f'Loyalty Points: {math.floor(pts)}')
        output_lines.append('')

        # Export JSON en parallèle (side effect)
        json_data.append({
            'customer_id': cid,
            'name': name,
            'total': total,
            'currency': currency,
            'loyalty_points': math.floor(pts)
        })

    output_lines.append(f'Grand Total: {grand_total:.2f} EUR')
    output_lines.append(f'Total Tax Collected: {total_tax_collected:.2f} EUR')

    result = '\n'.join(output_lines)
    
    # Side effects: print + file write
    print(result)
    
    # Export JSON surprise
    output_path = os.path.join(base, 'output.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)
    
    return result


if __name__ == '__main__':
    run()
