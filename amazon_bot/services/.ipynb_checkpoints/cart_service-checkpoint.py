from typing import Any, Dict, List, Optional
from amazon_bot.utils.io_utils import read_json, write_json
from amazon_bot.config import CART_JSON

def load_cart() -> Dict[str, Any]:
    return read_json(CART_JSON, {"items": []})

def save_cart(cart: Dict[str, Any]):
    write_json(CART_JSON, cart)