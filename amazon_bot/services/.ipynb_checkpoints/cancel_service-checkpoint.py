import csv
from datetime import datetime, timedelta
from typing import Dict
from amazon_bot.config import ORDERS_CSV, VARIANTS_CSV, PRODUCTS_CSV, REFUNDS_CSV, CANCEL_WINDOW_MIN
from amazon_bot.services.order_service import list_order_items
from amazon_bot.services.stock_service import reload_products_cache

def _orders_rows():
    with open(ORDERS_CSV, encoding="utf-8") as f:
        return list(csv.DictReader(f))

def _save_orders_rows(rows):
    with open(ORDERS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["order_number","status","subtotal_cents","shipping_cents","total_cents","created_at"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

def _parse_dt(s: str) -> datetime:
    try: return datetime.fromisoformat(s)
    except: return datetime.now()

def cancel_eligible(order_row: dict) -> bool:
    if order_row["status"] != "paid": return False
    created = _parse_dt(order_row.get("created_at",""))
    return (datetime.now() - created) <= timedelta(minutes=CANCEL_WINDOW_MIN)

def _restock_on_cancel(order_number: str):
    items = list_order_items(order_number)
    with open(VARIANTS_CSV, encoding="utf-8") as f:
        var_rows = list(csv.DictReader(f))
    for it in items:
        if it["variant_id"]:
            for row in var_rows:
                if int(row["variant_id"]) == it["variant_id"]:
                    row["stock"] = str(int(row["stock"]) + it["qty"])
    with open(VARIANTS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["variant_id","product_id","size","stock"])
        w.writeheader()
        for r in var_rows:
            w.writerow(r)

    with open(PRODUCTS_CSV, encoding="utf-8") as f:
        prod_rows = list(csv.DictReader(f))
    for it in items:
        if not it["variant_id"]:
            for row in prod_rows:
                if int(row["product_id"]) == it["product_id"]:
                    row["stock"] = str(int(row["stock"]) + it["qty"])
    with open(PRODUCTS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["product_id","name","category","price_cents","has_sizes","stock"])
        w.writeheader()
        for r in prod_rows:
            w.writerow(r)
    reload_products_cache()

def _create_refund(order_number: str, amount_cents: int, status: str = "pending"):
    next_id = 1
    with open(REFUNDS_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try: next_id = max(next_id, int(row["refund_id"]) + 1)
            except: pass
    processed = datetime.now().isoformat(timespec="seconds") if status == "completed" else ""
    with open(REFUNDS_CSV, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([next_id, order_number, int(amount_cents), status, processed])

def cancel_order(order_number: str) -> dict:
    rows = _orders_rows()
    row = next((r for r in rows if r["order_number"] == order_number), None)
    if not row: return {"ok": False, "msg": "No encontré ese pedido."}
    if row["status"] == "canceled": return {"ok": False, "msg": "Ese pedido ya está cancelado."}
    if not cancel_eligible(row): return {"ok": False, "msg": f"No se puede cancelar: fuera de la ventana de {CANCEL_WINDOW_MIN} min o ya procesado."}

    row["status"] = "canceled"
    _save_orders_rows(rows)
    _restock_on_cancel(order_number)
    total = int(row["total_cents"])
    _create_refund(order_number, total, status="pending")
    return {"ok": True, "msg": f"Pedido {order_number} cancelado. Reembolso de ${total/100:.2f} en proceso."}