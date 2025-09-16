import csv
from datetime import datetime
from typing import Any, Dict, List, Optional
from amazon_bot.utils.text_utils import gen_order_number
from amazon_bot.services.stock_service import product_price_cents, stock_available, adjust_stock_on_checkout, PRODUCTS
from amazon_bot.services.cart_service import load_cart, save_cart
from amazon_bot.config import ORDERS_CSV, ORDER_ITEMS_CSV

def cart_summary() -> str:
    cart = load_cart()
    if not cart["items"]:
        return "Tu carrito está vacío."
    lines, total = [], 0
    for i, it in enumerate(cart["items"], 1):
        p = next(p for p in PRODUCTS if p["product_id"] == it["product_id"])
        desc = f"{i}) {p['name']}"
        if it["size"]:
            desc += f" talla {it['size'].upper()}"
        desc += f" — {it['qty']} pza(s) — ${it['unit_price_cents']/100:.2f} c/u"
        lines.append(desc)
        total += it["unit_price_cents"] * it["qty"]
    lines.append(f"Total estimado: ${total/100:.2f}")
    return "\n".join(lines)

def cart_add(pid: int, qty: int, size: Optional[str]) -> tuple[bool,str]:
    p = next(p for p in PRODUCTS if p["product_id"] == pid)
    variant_id = None

    if p["has_sizes"]:
        if not size:
            return False, "Me falta la talla para ese producto."
        vs = [v for v in PRODUCTS if False]  # placeholder to keep linter calm
    # Ajuste real
    from amazon_bot.services.stock_service import list_variants
    if p["has_sizes"]:
        vs = [v for v in list_variants(pid) if v["size"] == size]
        if not vs:
            return False, "Esa talla no existe para este producto."
        if vs[0]["stock"] < qty:
            return False, f"No hay stock suficiente de talla {size}."
        variant_id = vs[0]["variant_id"]
    else:
        if (p["stock"] or 0) < qty:
            return False, "No hay stock suficiente."

    cart = load_cart()
    for it in cart["items"]:
        if it["product_id"] == pid and it.get("size") == size:
            new_qty = it["qty"] + qty
            if not stock_available(pid, size, new_qty):
                return False, "No hay stock suficiente para sumar esa cantidad."
            it["qty"] = new_qty
            save_cart(cart)
            return True, "¡Listo! Actualicé la cantidad en el carrito."

    cart["items"].append({
        "product_id": pid,
        "variant_id": variant_id,
        "size": size,
        "qty": qty,
        "unit_price_cents": product_price_cents(pid)
    })
    save_cart(cart)
    return True, "Agregué el artículo a tu carrito. 😉"

def cart_remove_index(idx: int) -> str:
    cart = load_cart()
    if not (1 <= idx <= len(cart["items"])):
        return "Índice inválido."
    cart["items"].pop(idx-1)
    save_cart(cart)
    return "Eliminé el artículo del carrito."

def cart_set_qty_index(idx: int, qty: int) -> str:
    cart = load_cart()
    if not (1 <= idx <= len(cart["items"])): return "Índice inválido."
    if qty < 1:
        cart["items"].pop(idx-1); save_cart(cart); return "Cantidad 0: artículo eliminado."
    it = cart["items"][idx-1]
    if not stock_available(it["product_id"], it.get("size"), qty): return "No hay stock suficiente."
    it["qty"] = qty; save_cart(cart); return "Actualicé la cantidad. ✅"

def cart_add_qty_index(idx: int, delta: int) -> str:
    cart = load_cart()
    if not (1 <= idx <= len(cart["items"])): return "Índice inválido."
    it = cart["items"][idx-1]
    new_qty = it["qty"] + max(1, delta)
    if not stock_available(it["product_id"], it.get("size"), new_qty): return "No hay stock suficiente."
    it["qty"] = new_qty; save_cart(cart); return "Aumenté la cantidad."

def cart_sub_qty_index(idx: int, delta: int) -> str:
    cart = load_cart()
    if not (1 <= idx <= len(cart["items"])): return "Índice inválido."
    it = cart["items"][idx-1]
    new_qty = it["qty"] - max(1, delta)
    if new_qty <= 0:
        cart["items"].pop(idx-1); save_cart(cart); return "La cantidad llegó a 0: artículo eliminado."
    if not stock_available(it["product_id"], it.get("size"), new_qty): return "Cantidad inválida."
    it["qty"] = new_qty; save_cart(cart); return "Reduje la cantidad."

def cart_clear() -> str:
    save_cart({"items": []}); return "Vacié tu carrito."

def checkout() -> str:
    cart = load_cart()
    if not cart["items"]:
        return "No tienes artículos en el carrito."

    from amazon_bot.services.stock_service import stock_available
    for it in cart["items"]:
        if not stock_available(it["product_id"], it.get("size"), it["qty"]):
            return "Parece que cambió el inventario. Ajusta cantidades, por favor."

    subtotal = sum(it["unit_price_cents"] * it["qty"] for it in cart["items"])
    shipping = 0
    total = subtotal + shipping
    order_number = gen_order_number()

    with open(ORDERS_CSV, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([order_number, "paid", subtotal, shipping, total, datetime.now().isoformat(timespec="seconds")])

    with open(ORDER_ITEMS_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for it in cart["items"]:
            w.writerow([order_number, it["product_id"], it.get("variant_id") or "", it.get("size") or "", it["qty"], it["unit_price_cents"]])

    adjust_stock_on_checkout(cart["items"])
    save_cart({"items": []})
    return f"¡Pedido confirmado! Número: {order_number}"

def list_orders() -> List[Dict[str, Any]]:
    orders = []
    with open(ORDERS_CSV, encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            row["subtotal_cents"] = int(row["subtotal_cents"])
            row["shipping_cents"] = int(row["shipping_cents"])
            row["total_cents"]    = int(row["total_cents"])
            orders.append(row)
    orders.sort(key=lambda x: x["created_at"], reverse=True)
    return orders

def list_order_items(order_number: str) -> List[Dict[str, Any]]:
    items = []
    with open(ORDER_ITEMS_CSV, encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            if row["order_number"] == order_number:
                row["product_id"]       = int(row["product_id"])
                row["variant_id"]       = int(row["variant_id"]) if row["variant_id"] else None
                row["qty"]              = int(row["qty"])
                row["unit_price_cents"] = int(row["unit_price_cents"])
                p = next(p for p in PRODUCTS if p["product_id"] == row["product_id"])
                row["product_name"]     = p["name"]
                items.append(row)
    return items