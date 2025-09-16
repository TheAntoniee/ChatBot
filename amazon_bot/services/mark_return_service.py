import csv
from datetime import datetime
from typing import Dict
from amazon_bot.config import RETURNS_CSV, REFUNDS_CSV
from amazon_bot.services.order_service import list_order_items

def mark_return_received(return_id: int) -> dict:
    with open(RETURNS_CSV, encoding="utf-8") as f:
        ret_rows = list(csv.DictReader(f))
    rr = next((r for r in ret_rows if r["return_id"] == str(return_id)), None)
    if not rr: return {"ok": False, "msg": f"No encuentro la devolución #{return_id}."}

    rr["status"] = "received"
    with open(RETURNS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["return_id","order_number","item_idx","product_id","variant_id","size","qty","reason","method","status","created_at"])
        w.writeheader()
        for r in ret_rows:
            w.writerow(r)

    order_number = rr["order_number"]
    item_idx = int(rr["item_idx"])
    qty = int(rr["qty"])
    items = list_order_items(order_number)
    if not (1 <= item_idx <= len(items)): return {"ok": False, "msg": "Índice de artículo inválido en la devolución."}
    it = items[item_idx-1]
    amount = it["unit_price_cents"] * qty

    with open(REFUNDS_CSV, encoding="utf-8") as f:
        ref_rows = list(csv.DictReader(f))
    found = None
    for rf in ref_rows:
        if rf["order_number"] == order_number and int(rf["amount_cents"]) == amount and rf["status"] in ("", "pending"):
            rf["status"] = "completed"
            rf["processed_at"] = datetime.now().isoformat(timespec="seconds")
            found = rf
            break
    if not found:
        next_id = 1
        for rf in ref_rows:
            try: next_id = max(next_id, int(rf["refund_id"]) + 1)
            except: pass
        with open(REFUNDS_CSV, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([next_id, order_number, amount, "completed", datetime.now().isoformat(timespec="seconds")])
    else:
        with open(REFUNDS_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["refund_id","order_number","amount_cents","status","processed_at"])
            w.writeheader()
            for r in ref_rows:
                w.writerow(r)

    return {"ok": True, "msg": f"Devolución #{return_id} marcada como recibida. Reembolso de ${amount/100:.2f} completado."}