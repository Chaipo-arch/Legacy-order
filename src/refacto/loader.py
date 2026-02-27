import csv
import os
from .models import Customer,Product,Promotion,ShippingZone,Order

def load_customers(path):
    customers = {}
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            customers[row[0]] = Customer (
                id= row[0],
                name= row[1],
                level= row[2] if len(row) > 2 else 'BASIC',
                shipping_zone= row[3] if len(row) > 3 else 'ZONE1',
                currency= row[4] if len(row) > 4 else 'EUR'
            )
    return customers


def load_products(path):
    products = {}
    f = open(path, 'r', encoding='utf-8')
    lines = f.readlines()
    f.close()
    for i in range(1, len(lines)):
        try:
            parts = lines[i].strip().split(',')
            products[parts[0]] = Product(
                id= parts[0],
                name= parts[1],
                category= parts[2],
                price= float(parts[3]),
                weight= float(parts[4]) if len(parts) > 4 else 1.0,
                taxable= parts[5].lower() == 'true' if len(parts) > 5 else True
            )
        except Exception:
            pass
    return products


def load_shipping_zones(path):
    shipping_zones = {}
    with open(path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            shipping_zones[row['zone']] = ShippingZone (
                zone= row['zone'],
                base= float(row['base']),
                per_kg= float(row.get('per_kg', 0.5))
            )
    return shipping_zones


def load_promotions(path):
    promotions = {}
    if not os.path.exists(path):
        return promotions
    try:
        with open(path, 'r') as f:
            content = f.read()
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if i == 0 or not line.strip():
                    continue
                p = line.split(',')
                promotions[p[0]] = Promotion (
                    code= p[0],
                    type= p[1],
                    value= p[2],
                    active= p[3] != 'false' if len(p) > 3 else True
                )
    except Exception:
        pass
    return promotions


def load_orders(path):
    orders = []
    with open(path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                qty = int(row['qty'])
                price = float(row['unit_price'])
                if qty <= 0 or price < 0:
                    continue
                orders.append(Order(
                    id=row['id'],
                    customer_id=row['customer_id'],
                    product_id=row['product_id'],
                    qty=qty,
                    unit_price=price,
                    date=row.get('date', ''),
                    promo_code=row.get('promo_code', ''),
                    time=row.get('time', '12:00')
                ))
            except Exception:
                continue
    return orders