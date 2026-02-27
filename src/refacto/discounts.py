from datetime import datetime

MAX_DISCOUNT = 200


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