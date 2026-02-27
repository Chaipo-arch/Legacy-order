import math
from datetime import datetime
from .models import ShippingZone
from .discounts import (
    compute_volume_discount,
    compute_weekend_bonus,
    compute_loyalty_discount,
    cap_and_adjust_discounts,
)

TAX = 0.2
SHIPPING_LIMIT = 50
handling_fee = 2.5
LOYALTY_RATIO = 0.01


def compute_loyalty_points(orders):
    loyalty_points = {}
    for o in orders:
        cid = o.customer_id
        if cid not in loyalty_points:
            loyalty_points[cid] = 0
        loyalty_points[cid] += o.qty * o.unit_price * LOYALTY_RATIO
    return loyalty_points


def apply_promotion_and_morning(o, products, promotions):
    prod = products.get(o.product_id)
    base_price = prod.price if prod else o.unit_price

    discount_rate = 0
    fixed_discount = 0
    if o.promo_code and o.promo_code in promotions:
        promo = promotions[o.promo_code]
        if promo.active:
            if promo.type == 'PERCENTAGE':
                discount_rate = float(promo.value) / 100
            elif promo.type == 'FIXED':
                fixed_discount = float(promo.value)

    line_total = o.qty * base_price * (1 - discount_rate) - fixed_discount * o.qty

    hour = int(o.time.split(':')[0])
    morning_bonus = 0
    if hour < 10:
        morning_bonus = line_total * 0.03
    line_total = line_total - morning_bonus

    return line_total, morning_bonus


def compute_tax(taxable, items, products):
    tax = 0.0
    all_taxable = True
    for item in items:
        prod = products.get(item.product_id)
        if prod and not prod.taxable:
            all_taxable = False
            break

    if all_taxable:
        tax = round(taxable * TAX, 2)
    else:
        for item in items:
            prod = products.get(item.product_id)
            if prod and prod.taxable:
                item_total = item.qty * prod.price
                tax += item_total * TAX
        tax = round(tax, 2)

    return tax


_DEFAULT_ZONE = ShippingZone(zone='DEFAULT', base=5.0, per_kg=0.5)

def compute_shipping(sub, weight, zone, shipping_zones):
    ship = 0.0
    if sub < SHIPPING_LIMIT:
        ship_zone = shipping_zones.get(zone, _DEFAULT_ZONE)

        if weight > 10:
            ship = ship_zone.base + (weight - 10) * ship_zone.per_kg
        elif weight > 5:
            ship = ship_zone.base + (weight - 5) * 0.3
        else:
            ship = ship_zone.base

        if zone in ('ZONE3', 'ZONE4'):
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
