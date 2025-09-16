import csv
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from amazon_bot.config import RETURNS_CSV, REFUNDS_CSV
from amazon_bot.services.order_service import list_orders, list_order_items

def _parse_dt(s: str) -> datetime:
    if not s:
        return datetime.now()
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return datetime.now()

def return_eligible(order_row: Dict[str, Any], days_window: int) -> bool:
    dt = _parse_dt(order_row.get("created_at", ""))
    return dt >= (datetime.now() - timedelta(days=days_window))

def _next_id(csv_path: str, field: str) -> int:
    next_id = 1
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try: next_id = max(next_id, int(row[field]) + 1)
            except: pass
    return next_id

def create_return(order_number: str, item_idx: int, qty: int, reason: str, method: str) -> Dict[str, Any]:
    items = list_order_items(order_number)
    if not (1 <= item_idx <= len(items)):
        return {"ok": False, "msg": "Índice de artículo inválido."}
    it = items[item_idx-1]
    if qty < 1 or qty > it["qty"]:
        return {"ok": False, "msg": f"Cantidad inválida (1–{it['qty']})."}

    rid = _next_id(RETURNS_CSV, "return_id")
    created_at = datetime.now().isoformat(timespec="seconds")

    with open(RETURNS_CSV, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            rid, order_number, item_idx, it["product_id"], it["variant_id"] or "", it.get("size") or "",
            qty, reason, method, "requested", created_at
        ])

    amount = it["unit_price_cents"] * qty
    ref_id = _next_id(REFUNDS_CSV, "refund_id")
    with open(REFUNDS_CSV, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([ref_id, order_number, amount, "pending", ""])

    return {"ok": True, "msg": f"Devolución #{rid} creada. Reembolso estimado ${amount/100:.2f} (pendiente)."}

def refund_status_text(order_number: Optional[str]=None) -> str:
    ods = list_orders()
    if not ods:
        return "No hay pedidos registrados."
    if order_number is None:
        order_number = ods[0]["order_number"]

    refunds, returns = [], []
    with open(REFUNDS_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["order_number"] == order_number:
                row["amount_cents"] = int(row["amount_cents"])
                refunds.append(row)
    with open(RETURNS_CSV, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["order_number"] == order_number:
                returns.append(row)

    if not refunds and not returns:
        return f"No hay devoluciones o reembolsos para el pedido {order_number}."

    lines = [f"Pedido {order_number} — Estatus:"]
    for rr in returns:
        lines.append(f"- Devolución #{rr['return_id']}: {rr['status']} (método: {rr['method']}, creado {rr['created_at']})")
    for rf in refunds:
        est = rf['status'] or 'pendiente'
        lines.append(f"- Reembolso #{rf['refund_id']}: ${rf['amount_cents']/100:.2f} — {est}")
    return "\n".join(lines)