import csv
from typing import Any, Dict, List, Optional
from amazon_bot.config import PRODUCTS_CSV, VARIANTS_CSV

def load_products() -> List[Dict[str, Any]]:
    out = []
    with open(PRODUCTS_CSV, encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            row["product_id"]  = int(row["product_id"])
            row["price_cents"] = int(row["price_cents"])
            row["has_sizes"]   = int(row["has_sizes"])
            row["stock"]       = int(row["stock"]) if row["stock"] != "" else None
            out.append(row)
    return out

def load_variants() -> Dict[int, List[Dict[str, Any]]]:
    var: Dict[int, List[Dict[str, Any]]] = {}
    with open(VARIANTS_CSV, encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            row["variant_id"] = int(row["variant_id"])
            row["product_id"] = int(row["product_id"])
            row["stock"]      = int(row["stock"])
            var.setdefault(row["product_id"], []).append(row)
    return var