# Promotions / Coupons System (Enhanced Version)
"""Defines simple percentage-based promo codes.
You can extend this later to time-based or city-based promos.
Referral codes are handled separately in trip records and admin analytics.
"""

PROMO_CODES = {
    "WELCOME50": 0.50,   # 50% off for new users
    "MALI10": 0.10,      # 10% off general promo
    "DRIVERBOOST20": 0.20, # 20% discount sponsored by platform
}

def apply_promo(code, fare):
    """Apply a percentage promo code to a fare.
    Returns (final_fare, discount_amount).
    """
    if not code:
        return fare, 0
    code = code.upper()
    if code in PROMO_CODES:
        discount = fare * PROMO_CODES[code]
        final = fare - discount
        return final, discount
    return fare, 0
