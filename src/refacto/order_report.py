"""
Order Report (refactorisé en modules)
Conserve le comportement legacy — run() retourne strictement la même sortie.
"""
import os
import math
import json

from .loader import (
    load_customers,
    load_products,
    load_shipping_zones,
    load_promotions,
    load_orders,
)
from .calculations import (
    compute_loyalty_points,
    apply_promotion_and_morning,
    compute_volume_discount,
    compute_weekend_bonus,
    compute_loyalty_discount,
    cap_and_adjust_discounts,
    compute_tax,
    compute_shipping,
    compute_handling,
    currency_rate,
)

TAX = 0.2
SHIPPING_LIMIT = 50
handling_fee = 2.5
MAX_DISCOUNT = 200


def run():
    base = os.path.dirname(__file__)
    cust_path = os.path.join(base, 'data', 'customers.csv')
    ord_path = os.path.join(base, 'data', 'orders.csv')
    prod_path = os.path.join(base, 'data', 'products.csv')
    ship_path = os.path.join(base, 'data', 'shipping_zones.csv')
    promo_path = os.path.join(base, 'data', 'promotions.csv')

    customers = load_customers(cust_path)
    products = load_products(prod_path)
    shipping_zones = load_shipping_zones(ship_path)
    promotions = load_promotions(promo_path)
    orders = load_orders(ord_path)

    # Loyalty
    loyalty_points = compute_loyalty_points(orders)

    # Grouping
    totals_by_customer = {}
    for o in orders:
        cid = o.customer_id
        prod = products.get(o.product_id)
        line_total, morning_bonus = apply_promotion_and_morning(o, products, promotions)

        if cid not in totals_by_customer:
            totals_by_customer[cid] = {
                'subtotal': 0.0,
                'items': [],
                'weight': 0.0,
                'promo_discount': 0.0,
                'morning_bonus': 0.0,
            }

        totals_by_customer[cid]['subtotal'] += line_total
        totals_by_customer[cid]['weight'] += (prod.weight if prod else 1.0) * o.qty
        totals_by_customer[cid]['items'].append(o)
        totals_by_customer[cid]['morning_bonus'] += morning_bonus

    output_lines = []
    json_data = []
    grand_total = 0.0
    total_tax_collected = 0.0

    sorted_customer_ids = sorted(totals_by_customer.keys())

    for cid in sorted_customer_ids:
        cust = customers.get(cid)
        name = cust.name if cust else 'Unknown'
        level = cust.level if cust else 'BASIC'
        zone = cust.shipping_zone if cust else 'ZONE1'
        currency = cust.currency if cust else 'EUR'

        sub = totals_by_customer[cid]['subtotal']

        disc = compute_volume_discount(sub, level)
        first_order_date = totals_by_customer[cid]['items'][0].date if totals_by_customer[cid]['items'] else ''
        disc = compute_weekend_bonus(disc, first_order_date)

        pts = loyalty_points.get(cid, 0)
        loyalty_discount = compute_loyalty_discount(pts)

        disc, loyalty_discount, total_discount = cap_and_adjust_discounts(disc, loyalty_discount)

        taxable = sub - total_discount
        tax = compute_tax(taxable, totals_by_customer[cid]['items'], products)

        ship = compute_shipping(sub, totals_by_customer[cid]['weight'], zone, shipping_zones)

        item_count = len(totals_by_customer[cid]['items'])
        handling = compute_handling(item_count)

        currency_rate_val = currency_rate(currency)
        total = round((taxable + tax + ship + handling) * currency_rate_val, 2)
        grand_total += total
        total_tax_collected += tax * currency_rate_val

        output_lines.append(f'Customer: {name} ({cid})')
        output_lines.append(f'Level: {level} | Zone: {zone} | Currency: {currency}')
        output_lines.append(f'Subtotal: {sub:.2f}')
        output_lines.append(f'Discount: {total_discount:.2f}')
        output_lines.append(f'  - Volume discount: {disc:.2f}')
        output_lines.append(f'  - Loyalty discount: {loyalty_discount:.2f}')
        if totals_by_customer[cid]['morning_bonus'] > 0:
            output_lines.append(f"  - Morning bonus: {totals_by_customer[cid]['morning_bonus']:.2f}")
        output_lines.append(f'Tax: {tax * currency_rate_val:.2f}')
        output_lines.append(f'Shipping ({zone}, {totals_by_customer[cid]["weight"]:.1f}kg): {ship:.2f}')
        if handling > 0:
            output_lines.append(f'Handling ({item_count} items): {handling:.2f}')
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

    output_path = os.path.join(base, 'output.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)

    return result


if __name__ == '__main__':
    run()