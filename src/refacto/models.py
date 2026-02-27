from dataclasses import dataclass, field

@dataclass
class Customer:
    id: str
    name: str
    level: str = 'BASIC'
    shipping_zone: str = 'ZONE1'
    currency: str = 'EUR'

@dataclass
class Product:
    id: str
    name: str
    category: str
    price: float
    weight: float = 1.0
    taxable: bool = True

@dataclass
class Order:
    id: str
    customer_id: str
    product_id: str
    qty: int
    unit_price: float
    date: str = ''
    promo_code: str = ''
    time: str = '12:00'

@dataclass
class Promotion:
    code: str
    type: str
    value: str
    active: bool = True

@dataclass
class ShippingZone:
    zone: str
    base: float
    per_kg: float = 0.5