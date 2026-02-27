"""
Refactored Order Report Generator
Golden Master Compatible
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


# =========================
# ====== LOADERS ==========
# =========================

def load_customers(path):
    customers = {}
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            customers[row[0]] = {
                'id': row[0],
                'name': row[1],
                'level': row[2] if len(row) > 2 else 'BASIC',
                'shipping_zone': row[3] if len(row) > 3 else 'ZONE1',
                'currency': row[4] if len(row) > 4 else 'EUR'
            }
    return customers


def load_products(path):
    products = {}
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines[1:]:
        try:
            parts = line.strip().split(',')
            products[parts[0]] = {
                'id': parts[0],
                'name': parts[1],
                'category': parts[2],
                'price': float(parts[3]),
                'weight': float(parts[4]) if len(parts) > 4 else 1.0,
                'taxable': parts[5].lower() == 'true' if len(parts) > 5 else True
            }
        except Exception:
            pass
    return products


def load_shipping_zones(path):
    zones = {}
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            zones[row['zone']] = {
                'zone': row['zone'],
                'base': float(row['base']),
                'per_kg': float(row.get('per_kg', 0.5))
            }
    return zones


def load_promotions(path):
    promotions = {}
    if not os.path.exists(path):
        return promotions

    try:
        with open(path, 'r') as f:
            lines = f.read().split('\n')
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
    except Exception:
        pass

    return promotions


def load_orders(path):
    orders = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                qty = int(row['qty'])
                price = float(row['unit_price'])

                if qty <= 0 or price < 0:
                    continue

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
            except Exception:
                continue
    return orders


# =========================
# ===== CALCULATIONS ======
# =========================

def compute_loyalty_points(orders):
    points = {}
    for o in orders:
        cid = o['customer_id']
        points.setdefault(cid, 0)
        points[cid] += o['qty'] * o['unit_price'] * LOYALTY_RATIO
    return points


def apply_promotion(order, product, promotions):
    base_price = product.get('price', order['unit_price'])

    discount_rate = 0
    fixed_discount = 0

    promo_code = order['promo_code']
    if promo_code and promo_code in promotions:
        promo = promotions[promo_code]
        if promo['active']:
            if promo['type'] == 'PERCENTAGE':
                discount_rate = float(promo['value']) / 100
            elif promo['type'] == 'FIXED':
                fixed_discount = float(promo['value'])

    line_total = order['qty'] * base_price * (1 - discount_rate)
    line_total -= fixed_discount * order['qty']

    hour = int(order['time'].split(':')[0])
    morning_bonus = 0
    if hour < 10:
        morning_bonus = line_total * 0.03
        line_total -= morning_bonus

    return line_total, morning_bonus


def compute_volume_discount(subtotal, level):
    disc = 0.0
    if subtotal > 50:
        disc = subtotal * 0.05
    if subtotal > 100:
        disc = subtotal * 0.10
    if subtotal > 500:
        disc = subtotal * 0.15
    if subtotal > 1000 and level == 'PREMIUM':
        disc = subtotal * 0.20
    return disc


def compute_loyalty_discount(points):
    discount = 0.0
    if points > 100:
        discount = min(points * 0.1, 50.0)
    if points > 500:
        discount = min(points * 0.15, 100.0)
    return discount


def compute_weekend_bonus(discount, first_date):
    if not first_date:
        return discount

    try:
        dt = datetime.strptime(first_date, '%Y-%m-%d')
        if dt.weekday() in (5, 6):
            return discount * 1.05
    except Exception:
        pass

    return discount


# =========================
# ========= RUN ===========
# =========================

def run():
    base = os.path.dirname(__file__)
    data_dir = os.path.join(base, 'data')

    customers = load_customers(os.path.join(data_dir, 'customers.csv'))
    products = load_products(os.path.join(data_dir, 'products.csv'))
    shipping_zones = load_shipping_zones(os.path.join(data_dir, 'shipping_zones.csv'))
    promotions = load_promotions(os.path.join(data_dir, 'promotions.csv'))
    orders = load_orders(os.path.join(data_dir, 'orders.csv'))

    loyalty_points = compute_loyalty_points(orders)

    totals = {}

    for o in orders:
        cid = o['customer_id']
        product = products.get(o['product_id'], {})

        line_total, morning_bonus = apply_promotion(o, product, promotions)

        totals.setdefault(cid, {
            'subtotal': 0.0,
            'weight': 0.0,
            'items': [],
            'morning_bonus': 0.0
        })

        totals[cid]['subtotal'] += line_total
        totals[cid]['weight'] += product.get('weight', 1.0) * o['qty']
        totals[cid]['items'].append(o)
        totals[cid]['morning_bonus'] += morning_bonus

    output_lines = []
    json_data = []
    grand_total = 0.0
    total_tax_collected = 0.0

    for cid in sorted(totals.keys()):
        cust = customers.get(cid, {})
        name = cust.get('name', 'Unknown')
        level = cust.get('level', 'BASIC')
        zone = cust.get('shipping_zone', 'ZONE1')
        currency = cust.get('currency', 'EUR')

        sub = totals[cid]['subtotal']

        disc = compute_volume_discount(sub, level)
        disc = compute_weekend_bonus(disc, totals[cid]['items'][0].get('date', '') if totals[cid]['items'] else '')

        pts = loyalty_points.get(cid, 0)
        loyalty_discount = compute_loyalty_discount(pts)

        total_discount = disc + loyalty_discount
        if total_discount > MAX_DISCOUNT:
            ratio = MAX_DISCOUNT / total_discount
            disc *= ratio
            loyalty_discount *= ratio
            total_discount = MAX_DISCOUNT

        taxable = sub - total_discount
        tax = round(taxable * TAX, 2)

        ship = 0.0
        if sub < SHIPPING_LIMIT:
            zone_data = shipping_zones.get(zone, {'base': 5.0, 'per_kg': 0.5})
            ship = zone_data['base']
        total = round(taxable + tax + ship, 2)

        grand_total += total
        total_tax_collected += tax

        output_lines.append(f'Customer: {name} ({cid})')
        output_lines.append(f'Subtotal: {sub:.2f}')
        output_lines.append(f'Total: {total:.2f} {currency}')
        output_lines.append(f'Loyalty Points: {math.floor(pts)}')
        output_lines.append('')

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

    print(result)

    with open(os.path.join(base, 'output.json'), 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)

    return result


if __name__ == '__main__':
    run()