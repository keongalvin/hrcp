# E-commerce Product Catalog

Manage product categories with inherited attributes.

```python
from hrcp import ResourceTree, PropagationMode, get_value

tree = ResourceTree(root_name="catalog")

# Store-wide defaults
tree.root.set_attribute("currency", "USD")
tree.root.set_attribute("tax_rate", 0.08)
tree.root.set_attribute("shipping", {"free_threshold": 50, "flat_rate": 5.99})
tree.root.set_attribute("return_policy", {"days": 30, "restocking_fee": 0})

# Electronics category
tree.create("/catalog/electronics", attributes={
    "warranty": {"months": 12},
    "return_policy": {"days": 15, "restocking_fee": 0.15}
})

tree.create("/catalog/electronics/computers", attributes={
    "warranty": {"months": 24}
})
tree.create("/catalog/electronics/computers/laptops", attributes={
    "shipping": {"free_threshold": 0}  # Free shipping on laptops
})

tree.create("/catalog/electronics/phones", attributes={
    "warranty": {"months": 12, "accidental_damage": False}
})

# Clothing category
tree.create("/catalog/clothing", attributes={
    "return_policy": {"days": 60}  # Extended returns
})
tree.create("/catalog/clothing/shoes")
tree.create("/catalog/clothing/outerwear")

def get_product_policies(tree, category_path):
    """Get all policies applicable to a product category."""
    category = tree.get(category_path)
    return {
        "currency": get_value(category, "currency", PropagationMode.INHERIT),
        "tax_rate": get_value(category, "tax_rate", PropagationMode.INHERIT),
        "shipping": get_value(category, "shipping", PropagationMode.MERGE),
        "warranty": get_value(category, "warranty", PropagationMode.MERGE),
        "return_policy": get_value(category, "return_policy", PropagationMode.MERGE),
    }

# Compare policies
laptop_policy = get_product_policies(tree, "/catalog/electronics/computers/laptops")
shoes_policy = get_product_policies(tree, "/catalog/clothing/shoes")

print("Laptop policies:")
print(f"  Free shipping: ${laptop_policy['shipping']['free_threshold']}")  # 0 (free)
print(f"  Warranty: {laptop_policy['warranty']['months']} months")         # 24
print(f"  Returns: {laptop_policy['return_policy']['days']} days")         # 15

print("\nShoes policies:")
print(f"  Free shipping: ${shoes_policy['shipping']['free_threshold']}")   # 50
print(f"  Warranty: {shoes_policy['warranty']}")                           # None
print(f"  Returns: {shoes_policy['return_policy']['days']} days")          # 60
```

## Key Patterns

- **Store defaults** (currency, tax, shipping) at root
- **Category overrides** for different product types
- **Deep category hierarchies** (electronics → computers → laptops)
- **MERGE** for policies allows partial customization
- **Missing attributes** (warranty on clothing) naturally return None
