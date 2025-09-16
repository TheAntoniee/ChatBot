from typing import Any, Dict, List, Optional
from amazon_bot.utils.text_utils import normalize
from amazon_bot.services.stock_service import PRODUCTS

def search_products(query: str) -> List[Dict[str, Any]]:
    q = normalize(query)
    results = []
    for p in PRODUCTS:
        if (q in normalize(p["name"])) or (q in normalize(p["category"])):
            results.append(p)
    return results or PRODUCTS

def find_product_by_index(results: List[Dict[str, Any]], idx: int) -> Optional[Dict[str, Any]]:
    if 1 <= idx <= len(results):
        return results[idx-1]
    return None