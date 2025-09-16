from datetime import datetime
from typing import Dict
from amazon_bot.services.order_service import list_orders, list_order_items

def _fmt_money(cents: int) -> str:
    return f"${cents/100:.2f}"

def _fmt_date(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso or ""

def orders_list_text() -> str:
    ods = list_orders()
    if not ods:
        return "Aún no tienes pedidos."
    lines = ["Tus pedidos (más recientes primero):"]
    for i, o in enumerate(ods, 1):
        lines.append(f"{i}) {o['order_number']} — {_fmt_money(int(o['total_cents']))} — {o['status']} — {_fmt_date(o['created_at'])}")
    lines.append("\nResponde con el número de la lista (ej. '1') o pega el número de pedido (123-1234567-1234567).")
    lines.append("Comandos: 'atrás', 'salir'.")
    return "\n".join(lines)

def order_detail_text(order_number: str) -> str:
    ods = [o for o in list_orders() if o["order_number"] == order_number]
    if not ods:
        return "No encontré ese pedido."
    o = ods[0]
    items = list_order_items(order_number)
    lines = [f"Pedido {order_number}",
             f"Fecha: {_fmt_date(o['created_at'])}",
             f"Estatus: {o['status']}",
             f"Subtotal: {_fmt_money(int(o['subtotal_cents']))}",
             f"Envío: {_fmt_money(int(o['shipping_cents']))}",
             f"Total: {_fmt_money(int(o['total_cents']))}",
             "\nArtículos:"]
    for it in items:
        size = f" talla {it['size'].upper()}" if it.get("size") else ""
        line_total = it["unit_price_cents"] * it["qty"]
        lines.append(f"- {it['product_name']}{size} × {it['qty']} — {_fmt_money(it['unit_price_cents'])} c/u = {_fmt_money(line_total)}")
    lines.append("\nAcciones rápidas: escribe 'reembolso' para ver el estatus de reembolso, "
                 "o 'devolver' para iniciar devolución de un artículo.")
    lines.append("También: 'atrás' (volver a la lista), 'salir'.")
    return "\n".join(lines)