import math
from datetime import datetime

TAX = 0.2
SHIPPING_LIMIT = 50
handling_fee = 2.5
MAX_DISCOUNT = 200
LOYALTY_RATIO = 0.01


def compute_loyalty_points(orders):
    loyalty_points = {}
    for o in orders:
        cid = o['customer_id']
        if cid not in loyalty_points:
            loyalty_points[cid] = 0
        loyalty_points[cid] += o['qty'] * o['unit_price'] * LOYALTY_RATIO
    return loyalty_points


def apply_promotion_and_morning(o, products, promotions):
    prod = products.get(o['product_id'], {})
    base_price = prod.get('price', o['unit_price'])

    promo_code = o.get('promo_code', '')
    discount_rate = 0
    fixed_discount = 0
    if promo_code and promo_code in promotions:
        promo = promotions[promo_code]
        if promo['active']:
            if promo['type'] == 'PERCENTAGE':
                discount_rate = float(promo['value']) / 100
            elif promo['type'] == 'FIXED':
                fixed_discount = float(promo['value'])

    line_total = o['qty'] * base_price * (1 - discount_rate) - fixed_discount * o['qty']

    hour = int(o['time'].split(':')[0])
    morning_bonus = 0
    if hour < 10:
        morning_bonus = line_total * 0.03
    line_total = line_total - morning_bonus

    return line_total, morning_bonus


def compute_volume_discount(sub, level):
    disc = 0.0
    if sub > 50:
        disc = sub * 0.05
    if sub > 100:
        disc = sub * 0.10
    if sub > 500:
        disc = sub * 0.15
    if sub > 1000 and level == 'PREMIUM':
        disc = sub * 0.20
    return disc


def compute_weekend_bonus(disc, first_order_date):
    if not first_order_date:
        return disc
    try:
        dt = datetime.strptime(first_order_date, '%Y-%m-%d')
        if dt.weekday() in (5, 6):
            return disc * 1.05
    except Exception:
        pass
    return disc


def compute_loyalty_discount(pts):
    loyalty_discount = 0.0
    if pts > 100:
        loyalty_discount = min(pts * 0.1, 50.0)
    if pts > 500:
        loyalty_discount = min(pts * 0.15, 100.0)
    return loyalty_discount


def cap_and_adjust_discounts(disc, loyalty_discount):
    total_discount = disc + loyalty_discount
    if total_discount > MAX_DISCOUNT:
        ratio = MAX_DISCOUNT / total_discount if total_discount > 0 else 1
        disc = disc * ratio
        loyalty_discount = loyalty_discount * ratio
        total_discount = MAX_DISCOUNT
    return disc, loyalty_discount, total_discount


def compute_tax(taxable, items, products):
    tax = 0.0
    # Vérifier si tous produits taxables
    all_taxable = True
    for item in items:
        prod = products.get(item['product_id'])
        if prod and prod.get('taxable', True) == False:
            all_taxable = False
            break

    if all_taxable:
        tax = round(taxable * TAX, 2)
    else:
        for item in items:
            prod = products.get(item['product_id'])
            if prod and prod.get('taxable', True) != False:
                item_total = item['qty'] * prod.get('price', item['unit_price'])
                tax += item_total * TAX
        tax = round(tax, 2)

    return tax


def compute_shipping(sub, weight, zone, shipping_zones):
    ship = 0.0
    if sub < SHIPPING_LIMIT:
        ship_zone = shipping_zones.get(zone, {'base': 5.0, 'per_kg': 0.5})
        base_ship = ship_zone['base']

        if weight > 10:
            ship = base_ship + (weight - 10) * ship_zone['per_kg']
        elif weight > 5:
            ship = base_ship + (weight - 5) * 0.3
        else:
            ship = base_ship

        if zone == 'ZONE3' or zone == 'ZONE4':
            ship = ship * 1.2
    else:
        if weight > 20:
            ship = (weight - 20) * 0.25
    return ship


def compute_handling(item_count):
    handling = 0.0
    if item_count > 10:
        handling = handling_fee
    if item_count > 20:
        handling = handling_fee * 2
    return handling


def currency_rate(currency):
    if currency == 'USD':
        return 1.1
    elif currency == 'GBP':
        return 0.85
    return 1.0
