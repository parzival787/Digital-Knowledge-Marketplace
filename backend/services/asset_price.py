from decimal import Decimal


def asset_price(value) -> Decimal:
    if type(value) not in (int, float, Decimal):
        raise ValueError("Invalid price")
    price = Decimal(str(value))
    if not price.is_finite() or not Decimal("0.01") <= price <= 100 or price != price.quantize(Decimal("0.01")):
        raise ValueError("Price must be 0.01–100 USDC with at most two decimal places")
    return price
