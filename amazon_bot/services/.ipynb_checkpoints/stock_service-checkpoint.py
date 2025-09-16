import csv
from typing import Any, Dict, List, Optional
from amazon_bot.config import PRODUCTS_CSV, VARIANTS_CSV
from amazon_bot.services.product_service import load_products, load_variants

PRODUCTS = load_products()
VARIANTS = load_variants()

def reload_products_cache():
    global PRODUCTS, VARIANTS
    PRODUCTS = load_products()
    VARIANTS = load_variants()

def product_price_cents(pid: int) -> int:
    for p in PRODUCTS:
        if p["product_id"] == pid:
            return p["price_cents"]
    raise KeyError(f"Producto {pid} no existe")

def list_variants(product_id: int) -> List[Dict[str, Any]]:
    return VARIANTS.get(product_id, [])

def stock_available(pid: int, size: Optional[str], qty: int) -> bool:
    p = next(p for p in PRODUCTS if p["product_id"] == pid)
    if p["has_sizes"]:
        vs = [v for v in list_variants(pid) if v["size"] == size]
        if not vs:
            return False
        return vs[0]["stock"] >= qty
    else:
        return (p["stock"] or 0) >= qty

def adjust_stock_on_checkout(items: List[Dict[str, Any]]):
    # 1) variantes
    with open(VARIANTS_CSV, encoding="utf-8") as f:
        var_rows = list(csv.DictReader(f))
    for it in items:
        if it["variant_id"]:
            for row in var_rows:
                if int(row["variant_id"]) == it["variant_id"]:
                    row["stock"] = str(int(row["stock"]) - it["qty"])
    with open(VARIANTS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["variant_id","product_id","size","stock"])
        w.writeheader()
        for r in var_rows:
            w.writerow(r)

    # 2) productos sin talla
    with open(PRODUCTS_CSV, encoding="utf-8") as f:
        prod_rows = list(csv.DictReader(f))
    for it in items:
        if not it["variant_id"]:
            for row in prod_rows:
                if int(row["product_id"]) == it["product_id"]:
                    row["stock"] = str(int(row["stock"]) - it["qty"])
    with open(PRODUCTS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["product_id","name","category","price_cents","has_sizes","stock"])
        w.writeheader()
        for r in prod_rows:
            w.writerow(r)

    reload_products_cache()