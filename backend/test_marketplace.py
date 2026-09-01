
from services.blockchain import (
    marketplace,
    has_purchased,
    get_purchase_count,
)

BUYER = "0x9202BfF93f8A46f7D9BAe982CB1c021e34E8dc66"

print("Marketplace address:", marketplace.address)

print("Testing hasPurchased...")
print(
    "hasPurchased(1, buyer):",
    has_purchased(1, BUYER)
)

print("Testing purchaseCount...")
print(
    "purchaseCount(1, buyer):",
    get_purchase_count(1, BUYER)
)

print("Marketplace connection successful!")