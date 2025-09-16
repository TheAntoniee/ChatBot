import csv, random
from datetime import datetime, timedelta
from typing import Optional
from amazon_bot.config import SHIPMENTS_CSV
from amazon_bot.services.order_service import list_orders

def _load_shipments():
    with open(SHIPMENTS_CSV, encoding="utf-8") as f:
        return list(csv.DictReader(f))

def _save_shipments(rows):
    with open(SHIPMENTS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["order_number","tracking_number","carrier","created_at"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

def _ensure_tracking(order_number: str):
    rows = _load_shipments()
    row = next((r for r in rows if r["order_number"] == order_number), None)
    if row: return row
    # Genera un tracking demo estilo Amazon Logistics
    tracking = f"TBA{random.randint(100000000, 999999999)}"
    new = {"order_number": order_number, "tracking_number": tracking, "carrier": "Amazon Logistics", "created_at": datetime.now().isoformat(timespec="seconds")}
    rows.append(new); _save_shipments(rows); return new

def tracking_link(order_number: Optional[str]) -> str:
    ods = list_orders()
    if not ods: return "No hay pedidos registrados."
    if order_number is None: order_number = ods[0]["order_number"]
    sh = _ensure_tracking(order_number)
    # Liga “tipo Amazon” (demo; no real): solo devolvemos la URL
    return f"https://www.amazon.com.mx/progress-tracker/package?orderId={order_number}&trackingId={sh['tracking_number']}"