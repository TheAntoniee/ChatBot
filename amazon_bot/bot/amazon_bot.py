# amazon_bot.py
from dataclasses import dataclass, field
from datetime import datetime
from importlib import import_module as _im
from typing import Any, Dict, List, Optional
import re

def _svc(name: str):
    """Importa amazon_bot.services.<name> (con fallback a services.<name>)."""
    try:
        return _im(f'amazon_bot.services.{name}')
    except ModuleNotFoundError:
        return _im(f'services.{name}')

# ============== Bootstrap ==============
from amazon_bot.services.bootstrap import bootstrap

# ============== NLU + utils ==============
from amazon_bot.nlu.recognizer import INTENTS
from amazon_bot.nlu.parsers import parse_qty, parse_size
from amazon_bot.utils.text_utils import normalize
from amazon_bot.nlu.fuzzy import fuzzy_boost
from amazon_bot.ui.tone import friendly_greeting, quick_options

# ============== Services ==============
from amazon_bot.services.search_service import search_products, find_product_by_index
from amazon_bot.services.stock_service import PRODUCTS, stock_available
from amazon_bot.services.order_service import (
    cart_summary, cart_add, cart_remove_index, cart_set_qty_index, cart_add_qty_index,
    cart_sub_qty_index, cart_clear, checkout, list_orders, list_order_items
)
from amazon_bot.services.user_service import (
    address_book_text, cards_text, add_address, set_default_address, delete_address,
    set_default_card, delete_card, add_card, default_address, list_cards, format_address_line
)
from amazon_bot.services.return_refund_service import create_return, refund_status_text, return_eligible
from amazon_bot.services.cancel_service import cancel_order, cancel_eligible
from amazon_bot.services.mark_return_service import mark_return_received
from amazon_bot.services.tracking_service import tracking_link
from amazon_bot.handlers.orders_text import orders_list_text, order_detail_text

# Para manipular el carrito por producto (sin índice)
from amazon_bot.services.cart_service import load_cart

# ================= Contextos =================

@dataclass
class Ctx:
    state: str = "INICIO"  # INICIO, LISTA, DETALLE, CONFIRMAR, CARRITO, ORDERS_LIST, ORDERS_DETAIL, ...
    last_results: List[Dict[str, Any]] = field(default_factory=list)
    current_product: Optional[Dict[str, Any]] = None
    qty: Optional[int] = None
    size: Optional[str] = None

@dataclass
class DevData:
    # Devoluciones (permite elegir por producto global, no sólo por pedido)
    order: Optional[str] = None
    items: List[Dict[str, Any]] = field(default_factory=list)  # items de un pedido o globales
    item_idx: Optional[int] = None
    qty: Optional[int] = None
    reason: Optional[str] = None
    method: Optional[str] = None
    scope: str = "BY_ORDER"  # "BY_ORDER" | "BY_PRODUCT"

@dataclass
class AdminCtx:
    state: str = ""
    a_name: Optional[str] = None
    a_phone: Optional[str] = None
    a_street: Optional[str] = None
    a_city: Optional[str] = None
    a_state: Optional[str] = None
    a_cp: Optional[str] = None
    c_brand: Optional[str] = None
    c_last4: Optional[str] = None

@dataclass
class CheckoutCtx:
    state: str = ""  # CHK_REVIEW, CHK_SELECT_PAY, CHK_ADD_BRAND, CHK_ADD_LAST4, CHK_ADDR_*
    selected_card_idx: Optional[int] = None
    add_brand: Optional[str] = None
    selected_addr_idx: Optional[int] = None
    # alta dirección inline
    a_name: Optional[str] = None
    a_phone: Optional[str] = None
    a_street: Optional[str] = None
    a_city: Optional[str] = None
    a_state: Optional[str] = None
    a_cp: Optional[str] = None

# ================= Bot =================

class AmazonBot:
    def __init__(self):
        # Crea / asegura los archivos de datos (data/, products/)
        bootstrap()

        self.ctx = Ctx()
        self.dev = DevData()
        self.admin = AdminCtx()
        self.chk = CheckoutCtx()
        self.abusive_count = 0
        self.offtopic_count = 0
        self.orders_current: Optional[str] = None
        self.cancel_order_num: Optional[str] = None
        self._home_seen = False

    # ---------- Helpers de sistema ----------
    def _reset_contexts(self, to_state: str = "INICIO") -> None:
        self.ctx = Ctx()
        self.dev = DevData()
        self.admin = AdminCtx()
        self.chk = CheckoutCtx()
        self.orders_current = None
        self.cancel_order_num = None
        self._home_seen = False
        self.abusive_count = 0
        self.offtopic_count = 0
        self.ctx.state = to_state

    def _saludo_text(self) -> str:
        h = datetime.now().hour
        if 6 <= h < 12: base = "¡Buenos días"
        elif 12 <= h < 19: base = "¡Buenas tardes"
        else: base = "¡Buenas noches"
        try:
            usvc = _svc("user_service")
            nombre = usvc.get_display_name()
            if nombre:
                return f"{base}, {nombre} 👋"
        except Exception:
            pass
        return f"{base} 👋"

    def _home_text(self, compact: bool = False) -> str:
        if compact:
            return "¿Qué te gustaría hacer ahora?\n" + quick_options()
        return friendly_greeting() + "\n\n" + quick_options()

    def _match_dev_item_by_name(self, u_norm: str) -> List[int]:
        q_tokens = [t for t in re.findall(r"\w+", u_norm) if len(t) >= 4]
        if not q_tokens:
            return []
        hits = []
        for i, it in enumerate(self.dev.items, 1):
            name = normalize(it.get("product_name", ""))
            if any(t in name for t in q_tokens):
                hits.append(i)
        return hits

    def _parse_index_word(self, u_norm: str, max_n: int) -> Optional[int]:
        m = re.search(r"\b(\d{1,2})\b", u_norm)
        if m:
            idx = int(m.group(1))
            if 1 <= idx <= max_n:
                return idx
        num_words = {
            "un":1,"uno":1,"una":1,"dos":2,"tres":3,"cuatro":4,"cinco":5,
            "seis":6,"siete":7,"ocho":8,"nueve":9,"diez":10,"once":11,
            "doce":12,"trece":13,"catorce":14,"quince":15
        }
        for w,v in num_words.items():
            if re.search(rf"\b{w}\b", u_norm) and 1 <= v <= max_n:
                return v
        ord_words = {
            "primero":1,"primera":1,"segundo":2,"segunda":2,"tercero":3,"tercera":3,
            "cuarto":4,"cuarta":4,"quinto":5,"quinta":5
        }
        for w,v in ord_words.items():
            if re.search(rf"\b{w}\b", u_norm) and 1 <= v <= max_n:
                return v
        return None
    # ---------- Helpers de categorías / catálogo ----------
    def _all_categories(self) -> List[str]:
        cats = []
        for p in PRODUCTS:
            c = (p.get("category") or "").strip()
            if c and c not in cats:
                cats.append(c)
        cats.sort()
        return cats

    def _categories_text(self) -> str:
        cats = self._all_categories()
        if not cats:
            return "Aún no tengo categorías cargadas. Prueba buscando algo (ej. 'playeras negras')."
        lines = ["Categorías disponibles:"]
        for i, c in enumerate(cats, 1):
            # muestra un ejemplo de producto
            sample = next((p for p in PRODUCTS if (p.get("category") or "").strip() == c), None)
            sample_txt = f" • Ej: {sample['name']}" if sample else ""
            lines.append(f"{i}) {c}{sample_txt}")
        lines.append("\nDi el número (ej. '1') o escribe el nombre de la categoría.")
        return "\n".join(lines)

    def _results_from_category(self, cat: str) -> List[Dict[str, Any]]:
        cat_norm = normalize(cat)
        res = [p for p in PRODUCTS if normalize(p.get("category") or "") == cat_norm]
        # Mapea al mismo formato que search_service regresa (ya son dicts con keys compatibles)
        # Si tu search_service hace algo extra, de todos modos estos dicts ya traen:
        # product_id, name, price_cents, has_sizes, category
        return res

    # ---------- Helpers de devoluciones por producto ----------
    def _recent_items_flat(self, max_orders: int = 10, max_items: int = 50) -> List[Dict[str, Any]]:
        """Aplana artículos recientes de varios pedidos para elegir por producto."""
        orders = list_orders()
        flat: List[Dict[str, Any]] = []
        for o in orders[:max_orders]:
            items = list_order_items(o["order_number"])
            for it in items:
                row = dict(it)
                row["__order_number"] = o["order_number"]  # anotar de qué pedido viene
                flat.append(row)
                if len(flat) >= max_items:
                    return flat
        return flat

    # ---------- Helpers de carrito por nombre ----------
    def _find_cart_index_by_name(self, name_fragment: str) -> Optional[int]:
        frag = normalize(name_fragment)
        cart = load_cart()
        for i, it in enumerate(cart["items"], 1):
            p = next((p for p in PRODUCTS if p["product_id"] == it["product_id"]), None)
            if not p: 
                continue
            if frag and frag in normalize(p["name"]):
                return i
        return None

    # ---------- Prompt por estado ----------
    def prompt(self) -> str:
        s = self.ctx.state

        # --- Checkout ---
        if self.chk.state == "CHK_REVIEW":
            return self._review_text()
        if self.chk.state == "CHK_SELECT_PAY":
            txt = cards_text(_svc("user_service").load_user())
            if "No tienes métodos" in txt:
                txt += "\n\nEscribe 'agregar' para registrar una tarjeta."
            else:
                txt += "\n\nDi 'usar 2' para elegir temporalmente durante este pago, o 'agregar'."
            return txt
        if self.chk.state == "CHK_ADD_BRAND": return "Marca de la tarjeta (Visa, MasterCard, American Express, Carnet):"
        if self.chk.state == "CHK_ADD_LAST4": return "Últimos 4 dígitos de la tarjeta:"
        if self.chk.state == "CHK_ADDR_MENU":
            txt = address_book_text(_svc("user_service").load_user())
            if "No tienes direcciones" in txt:
                txt += "\n\nEscribe 'agregar dirección' para registrar una."
            else:
                txt += "\n\nDi 'usar dirección 2' para elegir temporalmente durante este pago, o 'agregar dirección'."
            return txt
        if self.chk.state == "CHK_ADDR_ADD_NAME":  return "Nombre de la persona receptora:"
        if self.chk.state == "CHK_ADDR_ADD_PHONE": return "Teléfono (10 dígitos):"
        if self.chk.state == "CHK_ADDR_ADD_STREET":return "Calle y número:"
        if self.chk.state == "CHK_ADDR_ADD_CITY":  return "Ciudad/municipio:"
        if self.chk.state == "CHK_ADDR_ADD_STATE": return "Estado:"
        if self.chk.state == "CHK_ADDR_ADD_CP":    return "Código Postal (5 dígitos):"

        # --- Pedidos ---
        if s == "ORDERS_LIST": return orders_list_text()
        if s == "ORDERS_DETAIL": return order_detail_text(self.orders_current) if self.orders_current else "No hay pedido seleccionado."

        # --- Devoluciones ---
        if s == "DEV_PICK_GLOBAL":
            lines = ["¿Qué artículo quieres devolver? (recientes)"]
            for i, it in enumerate(self.dev.items, 1):
                size = f" talla {it['size'].upper()}" if it.get("size") else ""
                lines.append(f"{i}) {it['product_name']}{size} — {it['qty']} pza(s) — Pedido {it['__order_number']}")
            lines.append("Responde con el número (ej. '1'). También puedes pegar el número de pedido 123-1234567-1234567.")
            return "\n".join(lines)

        if s == "DEV_LISTA_ITEMS":
            lines = [f"Pedido {self.dev.order}. ¿Qué artículo quieres devolver?"]
            for i,it in enumerate(self.dev.items, 1):
                size = f" talla {it['size'].upper()}" if it.get("size") else ""
                lines.append(f"{i}) {it['product_name']}{size} — {it['qty']} pza(s)")
            lines.append("Responde con el número (ej. '1').")
            return "\n".join(lines)

        if s == "DEV_CANTIDAD":
            it = self.dev.items[self.dev.item_idx-1]
            return f"¿Cuántas unidades vas a devolver? (1–{it['qty']}). Puedes decir 'todo'."

        if s == "DEV_MOTIVO":
            return "¿Cuál es el motivo? (no es lo que pedí/dañado/defectuoso/no funciona/me equivoqué/tarde/otro)"

        if s == "DEV_METODO":
            return "Elige método: etiqueta de paquetería, punto de entrega, tienda o recolección."

        if s == "DEV_CONFIRMAR":
            it = self.dev.items[self.dev.item_idx-1]
            size = f" talla {it['size'].upper()}" if it.get("size") else ""
            return (f"Vas a devolver {self.dev.qty} pza(s) de '{it['product_name']}{size}' "
                    f"del pedido {self.dev.order}. Motivo: {self.dev.reason}. "
                    f"Método: {self.dev.method}. ¿Confirmas? (sí/no)")

        # --- Cancelación ---
        if s == "CANCEL_INICIO": return "Pega el número de pedido (123-1234567-1234567) o di 'el más reciente'."
        if s == "CANCEL_CONFIRMAR": return f"Vas a cancelar el pedido {self.cancel_order_num}. ¿Confirmas? (sí/no)"

        # --- Inicio / Compras / Carrito / Categorías ---
        if s == "INICIO":
            txt = self._home_text(compact=self._home_seen)
            self._home_seen = True
            return txt

        if s == "CATS":
            # listado de categorías
            return self._categories_text()

        if s == "CATS_LISTA":
            return "Elige un producto por número (ej. '1'), o escribe otra categoría/búsqueda."

        if s == "LISTA":
            return "Elige un producto por número (ej. '1'), o escribe otra búsqueda."

        if s == "DETALLE":
            p = self.ctx.current_product
            base = f"Seleccionado: {p['name']} — ${p['price_cents']/100:.2f}\n"
            if int(p.get("has_sizes") or 0):
                base += "Este producto requiere talla (XS,S,M,L,XL,XXL). "
            base += "Indica cantidad (ej. 'pon 2', 'par', 'docena') y, si aplica, la talla (ej. 'talla M')."
            return base

        if s == "CONFIRMAR":
            parts = [f"cantidad {self.ctx.qty}"]
            if self.ctx.size: parts.append(f"talla {self.ctx.size.upper()}")
            return f"¿Confirmas {', '.join(parts)}? (sí/no)"

        if s == "CARRITO":
            ayuda = (
                "\n\nPuedes hablar natural: 'quiero una playera más', 'quita dos calcetines', "
                "'cambia la sudadera a 3', 'elimina los tenis', 'vaciar carrito', 'pagar', "
                "o seguir buscando."
                "\n(Comandos clásicos: 'elimina 2', 'cambia cantidad del 1 a 3', "
                "'pon 2 al 1', 'suma 1 al 2', 'quita 1 al 2')."
            )
            return cart_summary() + ayuda

        if s == "FIN":
            return "¡Gracias por tu visita! 👋"

        return ""

    # ----- Auxiliares checkout -----
    def _review_text(self) -> str:
        lines = ["RESUMEN DEL PEDIDO", "-------------------", cart_summary()]
        # Dirección efectiva
        addrs = _svc("user_service").load_user().get("addresses", [])
        eff_addr = None
        if addrs:
            if self.chk.selected_addr_idx and 1 <= self.chk.selected_addr_idx <= len(addrs):
                eff_addr = addrs[self.chk.selected_addr_idx-1]
            else:
                eff_addr = next((a for a in addrs if a.get("is_default")), addrs[0])
        lines.append("\nDirección de entrega:")
        lines.append(format_address_line(eff_addr) if eff_addr else "(sin dirección — escribe 'agregar dirección')")
        # Métodos de pago
        cards = list_cards()
        if not cards:
            lines.append("\nMétodo de pago: (no tienes tarjetas guardadas)")
            lines.append("— Escribe 'agregar tarjeta' para registrar una.")
        else:
            lines.append("\nMétodo de pago:")
            for i, pm in enumerate(cards, 1):
                tag = []
                if pm.get("is_default"): tag.append("predeterminado")
                if self.chk.selected_card_idx and self.chk.selected_card_idx == i: tag.append("seleccionado")
                lines.append(f"{i}) {pm['brand'].upper()} ••{pm['last4']}" + (f" ({', '.join(tag)})" if tag else ""))
        lines.append(
           "\nOpciones: 'usar 2' (tarjeta), 'cambiar método', 'agregar tarjeta', "
           "'usar dirección 2', 'cambiar dirección', 'agregar dirección', "
           "'confirmar' / 'realiza tu pedido y paga', 'atrás', 'salir'."
        )
        lines.append("\n¿Continuamos? Escribe 'confirmar' o 'realiza tu pedido y paga'. También puedes decir 'cambiar dirección' o 'cambiar método'.")
        return "\n".join(lines)

    def _enter_checkout_review(self) -> str:
        self.chk.state = "CHK_REVIEW"; return self.prompt()

    def _exit_checkout(self):
        self.chk = CheckoutCtx()
        self.ctx.state = "INICIO"

    def _enter_orders(self) -> str:
        self.ctx.state = "ORDERS_LIST"; self.orders_current = None; return self.prompt()

    # ------------- Router principal -------------
    def handle(self, user: str) -> str:
        # ===== 0) Tres vistas del input =====
        u_raw = user
        u_norm = normalize(user)            # normalizado (sin fuzzy)
        u_boost = fuzzy_boost(u_norm)       # expandido (mejor para intents de negocio)

        # ===== 1) Si estoy bloqueado o "FIN": sólo permito reset/disculpa =====
        reset_re = INTENTS.get("RESET") or re.compile(
            r"\b(reiniciar|empezar(?: de nuevo)?|de nuevo|perd[oó]n(?:ame)?|disculp[ao]s?|lo siento|sorry)\b", re.I
        )
        if self.ctx.state in ("LOCKED", "FIN"):
            if reset_re.search(u_norm):
                self._reset_contexts(to_state="INICIO")
                return "Gracias. Retomemos desde el inicio. 🙌\n\n" + self.prompt()
            return ("La conversación está cerrada temporalmente. "
                    "Di 'reiniciar' o ofrece una disculpa para continuar.")

        # ===== 2) Saludos / smalltalk / nombre (con u_norm) =====
        if INTENTS.get("GREET") and INTENTS["GREET"].search(u_norm):
            return self._saludo_text() + "\n\n" + self.prompt()

        if INTENTS.get("SMALLTALK") and INTENTS["SMALLTALK"].search(u_norm):
            return "🙂 ¿En qué te ayudo?\n\n" + self.prompt()

        m_name = INTENTS.get("SET_NAME") and INTENTS["SET_NAME"].search(u_norm)
        if m_name:
            from amazon_bot.services.user_service import set_display_name
            nombre = m_name.group(1)
            msg = set_display_name(nombre)
            return msg + "\n\n" + self._saludo_text() + "\n\n" + self.prompt()

        # ===== 2.1) DEV_PICK_GLOBAL / DEV_LISTA_ITEMS — elegir artículo por nombre/ordinal/ID =====
        if self.ctx.state in ("DEV_PICK_GLOBAL", "DEV_LISTA_ITEMS"):
            # 1) Por nombre (ej. "playera", "cafetera")
            name_hits = self._match_dev_item_by_name(u_norm)
            if len(name_hits) == 1:
                self.dev.item_idx = name_hits[0]
                it = self.dev.items[self.dev.item_idx - 1]
                # fija pedido si viene desde global (acepta también __order_number)
                self.dev.order = it.get("order_number") or it.get("__order_number") or self.dev.order
                self.ctx.state = "DEV_CANTIDAD"
                return self.prompt()
            elif len(name_hits) > 1:
                # Desambiguar: acotar lista y volver a preguntar
                self.dev.items = [self.dev.items[i - 1] for i in name_hits]
                self.dev.item_idx = None
                return self.prompt()
        
            # 2) Por número/ordinal (ej. "uno", "la primera", "2")
            idx = self._parse_index_word(u_norm, len(self.dev.items))
            if idx:
                self.dev.item_idx = idx
                it = self.dev.items[idx - 1]
                # fija pedido si viene desde global (acepta también __order_number)
                self.dev.order = it.get("order_number") or it.get("__order_number") or self.dev.order
                self.ctx.state = "DEV_CANTIDAD"
                return self.prompt()
        
            # 3) Pegó un número de pedido (123-1234567-1234567)
            m_id = INTENTS.get("ORDER_BY_ID") and INTENTS["ORDER_BY_ID"].search(u_norm)
            if m_id:
                onum = m_id.group(0)
                sub = [x for x in self.dev.items if x.get("order_number") == onum]
                if not sub:
                    return ("Ese pedido no está en la lista. Elige un número, di 'la playera', "
                            "o pega otro ID (123-1234567-1234567).")
                self.dev.items = sub
                self.dev.order = onum
                if len(sub) == 1:
                    self.dev.item_idx = 1
                    self.ctx.state = "DEV_CANTIDAD"
                return self.prompt()
        
            # Nada coincidió
            return ("Dime el artículo: puedes decir 'uno', 'la playera', 'la cafetera', "
                    "'la primera', o pega el ID del pedido.")

        # ===== 2.2) Flujo de devolución: cantidad → motivo → método → confirmar
        if self.ctx.state == "DEV_CANTIDAD":
            it = self.dev.items[self.dev.item_idx-1]
            # 'todo'/'todas'/'todos'
            if re.search(r"\btod[oa]s?\b", u_norm):
                n = int(it.get("qty", 1))
            else:
                n = parse_qty(u_boost)
                if n is None:
                    return self.prompt()  # vuelve a preguntar la cantidad
            n = max(1, min(int(n), int(it.get("qty", 1))))
            self.dev.qty = n
            self.ctx.state = "DEV_MOTIVO"
            return self.prompt()

        if self.ctx.state == "DEV_MOTIVO":
            rn = u_norm
            if any(k in rn for k in ("no es lo que pedi","no es lo que pedí","no corresponde","equivocado")):
                self.dev.reason = "no es lo que pedí"
            elif any(k in rn for k in ("dañado","golpeado","quebrado","maltratado")):
                self.dev.reason = "dañado"
            elif "defectuos" in rn:
                self.dev.reason = "defectuoso"
            elif "no funciona" in rn or "no prende" in rn:
                self.dev.reason = "no funciona"
            elif any(k in rn for k in ("me equivoque","me equivoqué","ya no","no lo quiero")):
                self.dev.reason = "me equivoqué"
            elif "tarde" in rn or "retras" in rn:
                self.dev.reason = "tarde"
            elif "otro" in rn:
                self.dev.reason = "otro"
            else:
                return self.prompt()  # vuelve a pedir motivo
            self.ctx.state = "DEV_METODO"
            return self.prompt()

        if self.ctx.state == "DEV_METODO":
            mn = u_norm
            if "etiqueta" in mn:
                self.dev.method = "etiqueta de paquetería"
            elif "punto" in mn:
                self.dev.method = "punto de entrega"
            elif "tienda" in mn:
                self.dev.method = "tienda"
            elif "recole" in mn or "recog" in mn:
                self.dev.method = "recolección"
            else:
                return self.prompt()  # vuelve a pedir método
            # asegurar order si venimos de lista global
            it = self.dev.items[self.dev.item_idx-1]
            if not self.dev.order:
                self.dev.order = it.get("order_number") or it.get("__order_number")
            self.ctx.state = "DEV_CONFIRMAR"
            return self.prompt()

        if self.ctx.state == "DEV_CONFIRMAR":
            if INTENTS["CONFIRM"].search(u_norm):
                it = self.dev.items[self.dev.item_idx-1]
                order_num = self.dev.order or it.get("order_number") or it.get("__order_number")
                # Soportar firmas distintas de create_return
                try:
                    out = create_return(order_num, it, self.dev.qty, self.dev.reason, self.dev.method)
                except TypeError:
                    # firma alternativa: (order_num, item_idx, qty, reason, method)
                    out = create_return(order_num, self.dev.item_idx, self.dev.qty, self.dev.reason, self.dev.method)
                msg = out.get("msg") if isinstance(out, dict) else str(out)
                # reset
                self.dev = DevData()
                self.ctx.state = "INICIO"
                return msg + "\n\n" + self.prompt()
            if INTENTS["DENY"].search(u_norm):
                self.dev = DevData()
                self.ctx.state = "INICIO"
                return "Devolución cancelada.\n\n" + self.prompt()
            return "¿Confirmas? (sí/no)"
            
        # ===== 3) Filtros globales (usar u_norm para evitar falsos positivos) =====
        if INTENTS["OFF_TOPIC"].search(u_norm):
            self.offtopic_count += 1
            if self.offtopic_count >= 2:
                return "Puedo ayudarte con compras, carrito, pago, devoluciones, reembolsos, rastreo y administración. ¿Qué prefieres?"
            return "Creo que eso es otro tema 😅. Si quieres, dime 'mis pedidos', 'rastrear' o 'ver carrito'."
        self.offtopic_count = 0

        # ===== 11) Groserías (AL FINAL para evitar falsos positivos) =====
        if INTENTS["ABUSIVE"].search(u_norm):
            self.abusive_count += 1
            if self.abusive_count >= 2:
                self._reset_contexts(to_state="LOCKED")
                return ("He bloqueado la conversación por lenguaje inapropiado. "
                        "Di 'reiniciar' o ofrece una disculpa para continuar.")
            return "Mantengamos el respeto, por favor. ¿Seguimos?"

        # ===== 4) Comandos globales (EXIT/BACK/HELP) con u_norm =====
        if INTENTS["EXIT"].search(u_norm):
            # No cierres duro: deja en LOCKED para poder reiniciar
            self._reset_contexts(to_state="LOCKED")
            return "Conversación finalizada. Di 'reiniciar' si quieres volver a empezar."

        if INTENTS["BACK"].search(u_norm):
            # retroceso en devoluciones
            if self.ctx.state == "DEV_CONFIRMAR": self.ctx.state = "DEV_METODO"; return self.prompt()
            if self.ctx.state == "DEV_METODO": self.ctx.state = "DEV_MOTIVO"; return self.prompt()
            if self.ctx.state == "DEV_MOTIVO": self.ctx.state = "DEV_CANTIDAD"; return self.prompt()
            if self.ctx.state == "DEV_CANTIDAD": self.ctx.state = "DEV_LISTA_ITEMS" if self.dev.scope == "BY_ORDER" else "DEV_PICK_GLOBAL"; return self.prompt()
            if self.ctx.state == "DEV_LISTA_ITEMS": self.ctx.state = "INICIO"; return self.prompt()
            # checkout: volver al carrito
            if self.chk.state:
                self.chk = CheckoutCtx(); self.ctx.state = "CARRITO"; return self.prompt()
            # pedidos/cancelación
            if self.ctx.state in ("ORDERS_DETAIL",):
                return self._enter_orders()
            # categorías
            if self.ctx.state in ("CATS_LISTA",):
                self.ctx.state = "CATS"; return self.prompt()
            self.ctx.state = "INICIO"; return self.prompt()

        if INTENTS["HELP"].search(u_norm):
            return quick_options()

        # ===== 5) Accesos directos (carrito, switch) con u_norm =====
        if INTENTS["VIEW_CART"].search(u_norm):
            self.ctx.state = "CARRITO"; return self.prompt()

        m_switch = INTENTS["SWITCH"].search(u_norm)
        if m_switch:
            target = normalize(m_switch.group(3))
            if target in ("comprar","buscar"):
                self.ctx.state="INICIO"; return "Perfecto, cambiamos a compras. " + self.prompt()
            if target in ("carrito","carro"):
                self.ctx.state="CARRITO"; return "Aquí está tu carrito:\n\n" + self.prompt()
            if target == "pagar":
                from amazon_bot.services.cart_service import load_cart
                if load_cart()["items"]:
                    return self._enter_checkout_review()
                return checkout() + "\n\n" + self.prompt()
            if target in ("devolver","reembolso","pedidos","pedido","direcciones","pagos","pago","rastrear"):
                return "¡Anotado! Podemos hacerlo enseguida. Dime, ¿quieres mis pedidos, devolver, reembolso, rastrear, direcciones o pagos?"
            return "Cambio entendido, pero no reconocí la operación. " + quick_options()

        # ===== 6) Flujos globales que pueden entrar desde cualquier lugar (usar u_norm) =====
        # Rastreo (sólo liga)
        if INTENTS["TRACK_ENTER"].search(u_norm):
            m = INTENTS["ORDER_ID_OR_RECENT"].search(u_norm)
            if not m:
                ods = list_orders()
                if not ods: return "No hay pedidos para rastrear aún."
                return "¿Qué pedido quieres rastrear? Pega el número (123-1234567-1234567) o di 'el más reciente'."
            key = m.group(1)
            order_num = None if any(k in key for k in ("reciente","ultimo","último","más reciente","mas reciente")) else key
            link = tracking_link(order_num)
            return f"Aquí tienes la liga de rastreo 📦: {link}"

        # Atajo robusto: "ver reembolso", "estatus del reembolso", etc.
        if INTENTS.get("REFUND_STATUS") and INTENTS["REFUND_STATUS"].search(u_norm) or (
            "reembolso" in u_norm and any(w in u_norm for w in ("ver","estatus","status","como va","cómo va"))
        ):
            self.ctx.state = "REFUND_INFO"
            m = INTENTS["ORDER_ID_OR_RECENT"].search(u_norm)
            if not m:
                ods = list_orders()
                if not ods:
                    self.ctx.state = "INICIO"; return "No hay pedidos registrados."
                lines = ["Pedidos (más recientes primero):"]
                for i,o in enumerate(ods,1):
                    lines.append(f"{i}) {o['order_number']} — ${o['total_cents']/100:.2f}")
                lines.append("Pega el número de pedido o di 'el más reciente'.")
                return "\n".join(lines)
            key = m.group(1)
            order_num = None if any(k in key for k in ("reciente","ultimo","último")) else key
            msg = refund_status_text(order_num)
            self.ctx.state = "INICIO"
            return msg + "\n\n" + self.prompt()

        # Devoluciones (permitir entrar por producto o por pedido)
        if INTENTS.get("DEV_START") and INTENTS["DEV_START"].search(u_norm) or "devol" in u_norm:
            # Si pega número de pedido, vamos por pedido; si no, lista global por producto
            m = INTENTS["ORDER_ID_OR_RECENT"].search(u_norm)
            if m:
                key = m.group(1)
                if any(k in key for k in ("reciente","ultimo","último")):
                    ods = list_orders()
                    if not ods: self.ctx.state = "INICIO"; return "No hay pedidos registrados."
                    self.dev = DevData(order=ods[0]["order_number"], items=list_order_items(ods[0]["order_number"]), scope="BY_ORDER")
                    self.ctx.state = "DEV_LISTA_ITEMS"; return self.prompt()
                # pedido específico
                found = [o for o in list_orders() if o["order_number"] == key]
                if not found: return "No ubico ese pedido. Verifica el formato 123-1234567-1234567."
                self.dev = DevData(order=found[0]["order_number"], items=list_order_items(found[0]["order_number"]), scope="BY_ORDER")
                self.ctx.state = "DEV_LISTA_ITEMS"; return self.prompt()
            # escoger por producto global
            flat = self._recent_items_flat()
            if not flat:
                return "No tengo artículos recientes para devolver. ¿Quizá quieras ver 'mis pedidos'?"
            self.dev = DevData(order=None, items=flat, scope="BY_PRODUCT")
            self.ctx.state = "DEV_PICK_GLOBAL"; return self.prompt()

        # Cancelación
        if INTENTS["CANCEL_START"].search(u_norm) and self.ctx.state not in ("CANCEL_INICIO","CANCEL_CONFIRMAR"):
            self.ctx.state = "CANCEL_INICIO"; return self.prompt()
        if self.ctx.state == "CANCEL_INICIO":
            m = INTENTS["ORDER_ID_OR_RECENT"].search(u_norm)
            if not m:
                ods = list_orders()
                if not ods:
                    self.ctx.state = "INICIO"; return "No hay pedidos para cancelar."
                lines = ["Pedidos (más recientes primero):"]
                for i,o in enumerate(ods,1):
                    lines.append(f"{i}) {o['order_number']} — ${int(o['total_cents'])/100:.2f} — {o['status']}")
                lines.append("Pega el número de pedido o di 'el más reciente'.")
                return "\n".join(lines)
            key = m.group(1)
            if any(k in key for k in ("reciente","ultimo","último")):
                ods = list_orders()
                if not ods:
                    self.ctx.state = "INICIO"; return "No hay pedidos registrados."
                chosen = ods[0]
            else:
                found = [o for o in list_orders() if o["order_number"] == key]
                if not found: return "No ubico ese pedido. Verifica el formato 123-1234567-1234567."
                chosen = found[0]
            if not cancel_eligible(chosen):
                self.ctx.state = "INICIO"; return "Ese pedido ya no se puede cancelar (ventana expirada o ya procesado)."
            self.cancel_order_num = chosen["order_number"]
            self.ctx.state = "CANCEL_CONFIRMAR"; return self.prompt()
        if self.ctx.state == "CANCEL_CONFIRMAR":
            if INTENTS["CONFIRM"].search(u_norm):
                out = cancel_order(self.cancel_order_num); self.ctx.state = "INICIO"; self.cancel_order_num = None
                return out["msg"] + "\n\n" + self.prompt()
            if INTENTS["DENY"].search(u_norm):
                self.ctx.state = "INICIO"; self.cancel_order_num = None
                return "Cancelación abortada.\n\n" + self.prompt()
            return "¿Confirmas cancelar el pedido? (sí/no)"

        # Marcar devolución recibida #ID
        m_rcv = INTENTS["RETURN_MARK_RECEIVED"].search(u_norm) if INTENTS.get("RETURN_MARK_RECEIVED") else None
        if m_rcv:
            rid_txt = m_rcv.group("rid")
            if not rid_txt: return "Dime el número de devolución, ej. 'marcar devolución #1 recibida'."
            out = mark_return_received(int(rid_txt))
            msg = out["msg"]
            try:
                orders = list_orders()
                if orders: msg += "\n\n" + refund_status_text(orders[0]["order_number"])
            except Exception:
                pass
            return msg

        # Mis pedidos
        if INTENTS["ORDERS_ENTER"].search(u_norm) and self.ctx.state not in ("ORDERS_LIST","ORDERS_DETAIL"):
            self.ctx.state = "ORDERS_LIST"; self.orders_current = None; return self.prompt()
        if self.ctx.state == "ORDERS_LIST":
            if INTENTS["BACK"].search(u_norm): self.ctx.state = "INICIO"; return self.prompt()
            m = INTENTS["SELECT_N"].search(u_norm)
            if m:
                idx = int(m.group("idx")); ods = list_orders()
                if not (1 <= idx <= len(ods)): return "Índice inválido. Elige un número de la lista."
                self.ctx.state = "ORDERS_DETAIL"; self.orders_current = ods[idx-1]["order_number"]; return self.prompt()
            m_id = INTENTS["ORDER_BY_ID"].search(u_norm)
            m_recent = INTENTS["ORDER_ID_OR_RECENT"].search(u_norm)
            if m_id or m_recent:
                if m_recent and any(k in m_recent.group(1) for k in ("reciente","ultimo","último")):
                    ods = list_orders()
                    if not ods: self.ctx.state = "INICIO"; return "No hay pedidos registrados."
                    self.ctx.state = "ORDERS_DETAIL"; self.orders_current = ods[0]["order_number"]; return self.prompt()
                key = (m_id.group(0) if m_id else m_recent.group(1))
                ods = [o for o in list_orders() if o["order_number"] == key]
                if not ods: return "No ubico ese pedido. Verifica el formato 123-1234567-1234567."
                self.ctx.state = "ORDERS_DETAIL"; self.orders_current = ods[0]["order_number"]; return self.prompt()
            # salir a otros flujos (usa u_norm) → re-enrutar con el texto original
            if any(INTENTS[k].search(u_norm) for k in ("VIEW_CART","SEARCH","PAY","PROCEED_PAY","DEV_START","REFUND_STATUS","ADMIN_DIR_ENTER","ADMIN_PAGO_ENTER")):
                self.ctx.state = "INICIO"; return self.handle(u_raw)
            return self.prompt()

        if self.ctx.state == "ORDERS_DETAIL":
            if INTENTS["BACK"].search(u_norm): self.ctx.state = "ORDERS_LIST"; return self.prompt()
            if INTENTS["REFUND_STATUS"].search(u_norm) or ("reembolso" in u_norm and "ver" in u_norm):
                return refund_status_text(self.orders_current) + "\n\n" + self.prompt()
            if INTENTS["DEV_START"].search(u_norm) or "devol" in u_norm:
                row = next((o for o in list_orders() if o["order_number"] == self.orders_current), None)
                if not row: return "No encuentro el pedido en tu historial."
                from amazon_bot.config import RETURN_WINDOW_DAYS
                if not return_eligible(row, RETURN_WINDOW_DAYS):
                    self.ctx.state = "INICIO"; return "Ese pedido ya no es elegible para devolución." + "\n\n" + self.prompt()
                self.dev = DevData(order=self.orders_current, items=list_order_items(self.orders_current), scope="BY_ORDER")
                self.ctx.state = "DEV_LISTA_ITEMS"; return self.prompt()
            m = INTENTS["ORDER_BY_ID"].search(u_norm)
            if m: self.ctx.state = "ORDERS_DETAIL"; self.orders_current = m.group(0); return self.prompt()
            if any(INTENTS[k].search(u_norm) for k in ("VIEW_CART","SEARCH","PAY","PROCEED_PAY","ADMIN_DIR_ENTER","ADMIN_PAGO_ENTER")):
                self.ctx.state = "INICIO"; return self.handle(u_raw)
            return self.prompt()

        # ===== 7) Checkout (iniciar) =====
        # A partir de aquí usamos u_boost para intents de negocio
        u = u_boost

        if (INTENTS["PAY"].search(u) or INTENTS["PROCEED_PAY"].search(u)) and not self.chk.state:
            from amazon_bot.services.cart_service import load_cart
            if not load_cart()["items"]:
                return checkout() + "\n\n" + self.prompt()
            return self._enter_checkout_review()

        # ===== 8) Checkout estados =====
        if self.chk.state == "CHK_REVIEW":
            if INTENTS["CONFIRM"].search(u) or INTENTS["CONFIRM_PAY"].search(u):
                addrs = _svc("user_service").load_user().get("addresses", [])
                if not addrs:
                    self.chk.state = "CHK_ADDR_ADD_NAME"; return "No tienes dirección registrada. Vamos a agregar una.\n" + self.prompt()
                cards = list_cards()
                if not cards:
                    self.chk.state = "CHK_ADD_BRAND"; return "No tienes tarjetas guardadas. Vamos a agregar una.\n" + self.prompt()

                if self.chk.selected_addr_idx and 1 <= self.chk.selected_addr_idx <= len(addrs):
                    addr = addrs[self.chk.selected_addr_idx-1]
                else:
                    addr = next((a for a in addrs if a.get("is_default")), addrs[0])

                if self.chk.selected_card_idx and 1 <= self.chk.selected_card_idx <= len(cards):
                    card = cards[self.chk.selected_card_idx - 1]
                else:
                    card = next((c for c in cards if c.get("is_default")), cards[0])

                msg = checkout()
                self._exit_checkout()
                return msg + f"\nEnviaremos a: {format_address_line(addr)}\nPagado con {card['brand'].upper()} ••{card['last4']}.\n\n" + self.prompt()

            if INTENTS["PAY_CHANGE"].search(u):
                self.chk.state = "CHK_SELECT_PAY"; return self.prompt()
            m = INTENTS["PAY_USE_INDEX"].search(u)
            if m:
                idx = int(m.group("idx"))
                if not (1 <= idx <= len(list_cards())): return "Índice de tarjeta inválido. Prueba con 'usar 1' o 'agregar tarjeta'."
                self.chk.selected_card_idx = idx
                return self._review_text()

            if INTENTS["PAY_ADDR_CHANGE"].search(u):
                self.chk.state = "CHK_ADDR_MENU"; return self.prompt()
            m = INTENTS["PAY_ADDR_USE_INDEX"].search(u)
            if m:
                idx = int(m.group("idx"))
                addrs = _svc("user_service").load_user().get("addresses", [])
                if not (1 <= idx <= len(addrs)): return "Índice de dirección inválido. Prueba con 'usar dirección 1' o 'agregar dirección'."
                self.chk.selected_addr_idx = idx
                return self._review_text()

            if INTENTS["ADD_WORD"].search(u) and INTENTS["ADDR_WORD"].search(u):
                self.chk.state = "CHK_ADDR_ADD_NAME"; return self.prompt()
            if INTENTS["ADD_WORD"].search(u) and INTENTS["BRAND"].search(u):
                self.chk.state = "CHK_ADD_BRAND"; return self.prompt()
            if INTENTS["ADD_WORD"].search(u):
                return "¿Quieres agregar tarjeta o agregar dirección?"

            if INTENTS["PAY"].search(u):
                return "Si ya revisaste, escribe 'confirmar' para completar tu pedido, o 'cambiar método'/'agregar'."
            return self._review_text()

        if self.chk.state == "CHK_SELECT_PAY":
            m = INTENTS["PAY_USE_INDEX"].search(u)
            if m:
                idx = int(m.group("idx"))
                if not (1 <= idx <= len(list_cards())): return "Índice inválido. Di 'usar 1' o 'agregar'."
                self.chk.selected_card_idx = idx; self.chk.state = "CHK_REVIEW"; return self.prompt()
            if INTENTS["ADD_WORD"].search(u):
                self.chk.state = "CHK_ADD_BRAND"; return self.prompt()
            return self.prompt()

        if self.chk.state == "CHK_ADD_BRAND":
            m = INTENTS["BRAND"].search(u)
            if not m: return "Marca no reconocida. Usa: Visa, MasterCard, American Express o Carnet."
            self.chk.add_brand = m.group(1); self.chk.state = "CHK_ADD_LAST4"; return self.prompt()

        if self.chk.state == "CHK_ADD_LAST4":
            m = INTENTS["LAST4"].search(u)
            if not m: return "Los últimos 4 dígitos deben ser 4 números:"
            msg = add_card(self.chk.add_brand, m.group(1))
            self.chk.selected_card_idx = len(list_cards())
            self.chk.state = "CHK_REVIEW"; return msg + "\n\n" + self.prompt()

        if self.chk.state == "CHK_ADDR_MENU":
            m = INTENTS["PAY_ADDR_USE_INDEX"].search(u)
            if m:
                idx = int(m.group("idx"))
                addrs = _svc("user_service").load_user().get("addresses", [])
                if not (1 <= idx <= len(addrs)): return "Índice inválido. Di 'usar dirección 1' o 'agregar dirección'."
                self.chk.selected_addr_idx = idx; self.chk.state = "CHK_REVIEW"; return self.prompt()
            if INTENTS["ADD_WORD"].search(u) and INTENTS["ADDR_WORD"].search(u):
                self.chk.state = "CHK_ADDR_ADD_NAME"; return self.prompt()
            if INTENTS["ADD_WORD"].search(u):
                return "¿Agregar dirección? Di 'agregar dirección' o 'usar dirección 1'."
            m = INTENTS["SETDEF_IDX"].search(u)
            if m:
                idx = int(m.group("idx")); msg = set_default_address(idx); return msg + "\n\n" + self.prompt()
            m = INTENTS["DEL_IDX"].search(u)
            if m:
                idx = int(m.group("idx")); msg = delete_address(idx); return msg + "\n\n" + self.prompt()
            return self.prompt()

        if self.chk.state == "CHK_ADDR_ADD_NAME":
            name = u_raw.strip()
            if not name: return "Nombre de la persona receptora:"
            self.chk.a_name = name; self.chk.state = "CHK_ADDR_ADD_PHONE"; return self.prompt()
        if self.chk.state == "CHK_ADDR_ADD_PHONE":
            digits = re.sub(r"\D","", u_raw)
            if not re.fullmatch(r"\d{10}", digits): return "Teléfono inválido. Debe tener 10 dígitos:"
            self.chk.a_phone = digits; self.chk.state = "CHK_ADDR_ADD_STREET"; return self.prompt()
        if self.chk.state == "CHK_ADDR_ADD_STREET":
            street = u_raw.strip()
            if not street: return "Calle y número, por favor:"
            self.chk.a_street = street; self.chk.state = "CHK_ADDR_ADD_CITY"; return self.prompt()
        if self.chk.state == "CHK_ADDR_ADD_CITY":
            city = u_raw.strip()
            if not city: return "Ciudad/municipio, por favor:"
            self.chk.a_city = city; self.chk.state = "CHK_ADDR_ADD_STATE"; return self.prompt()
        if self.chk.state == "CHK_ADDR_ADD_STATE":
            st = u_raw.strip()
            if not st: return "Estado, por favor:"
            self.chk.a_state = st; self.chk.state = "CHK_ADDR_ADD_CP"; return self.prompt()
        if self.chk.state == "CHK_ADDR_ADD_CP":
            cp = u_raw.strip()
            if not re.fullmatch(r"\d{5}", cp): return "CP inválido. Debe tener 5 dígitos:"
            self.chk.a_cp = cp
            msg = add_address(self.chk.a_name, self.chk.a_phone, self.chk.a_street, self.chk.a_city, self.chk.a_state, self.chk.a_cp)
            addrs = _svc("user_service").load_user().get("addresses", [])
            self.chk.selected_addr_idx = len(addrs)
            self.chk.a_name = self.chk.a_phone = self.chk.a_street = self.chk.a_city = self.chk.a_state = self.chk.a_cp = None
            self.chk.state = "CHK_REVIEW"; return msg + "\n\n" + self._review_text()

        # ===== 9) Administración (direcciones/pagos) =====
        if INTENTS["ADMIN_DIR_ENTER"].search(u) and not self.admin.state:
            self.admin.state = "DIR_MENU"
            from amazon_bot.services.user_service import load_user
            return address_book_text(load_user()) + "\n\nOpciones: 'agregar', 'elimina 2', 'predeterminada 1', 'atrás' o 'salir'."
        if INTENTS["ADMIN_PAGO_ENTER"].search(u) and not self.admin.state:
            self.admin.state = "PAGO_MENU"
            from amazon_bot.services.user_service import load_user
            return cards_text(load_user()) + "\n\nOpciones: 'agregar', 'elimina 2', 'predeterminado 1', 'atrás' o 'salir'."

        if self.admin.state.startswith("DIR_"):
            s = self.admin.state
            from amazon_bot.services.user_service import load_user
            if s == "DIR_MENU":
                if INTENTS["ADD_WORD"].search(u):
                    self.admin.state = "DIR_ADD_NAME"; return "Nombre de la persona receptora:"
                m = INTENTS["DEL_IDX"].search(u)
                if m:
                    idx = int(m.group("idx")); msg = delete_address(idx)
                    return msg + "\n\n" + address_book_text(load_user()) + "\n\nOpciones: 'agregar', 'elimina 2', 'predeterminada 1', 'atrás' o 'salir'."
                m = INTENTS["SETDEF_IDX"].search(u)
                if m:
                    idx = int(m.group("idx")); msg = set_default_address(idx)
                    return msg + "\n\n" + address_book_text(load_user()) + "\n\nOpciones: 'agregar', 'elimina 2', 'predeterminada 1', 'atrás' o 'salir'."
                if INTENTS["ADMIN_PAGO_ENTER"].search(u):
                    self.admin.state = "PAGO_MENU"; return cards_text(load_user()) + "\n\nOpciones: 'agregar', 'elimina 2', 'predeterminado 1', 'atrás' o 'salir'."
                if INTENTS["ADMIN_DIR_ENTER"].search(u):
                    return address_book_text(load_user()) + "\n\nOpciones: 'agregar', 'elimina 2', 'predeterminada 1', 'atrás' o 'salir'."
                return "¿Qué deseas hacer en direcciones? 'agregar', 'elimina 2' o 'predeterminada 1'."
            if s == "DIR_ADD_NAME":
                self.admin.a_name = u_raw.strip() if u_raw.strip() else None
                if not self.admin.a_name: return "Dame un nombre válido:"
                self.admin.state = "DIR_ADD_PHONE"; return "Teléfono (10 dígitos):"
            if s == "DIR_ADD_PHONE":
                digits = re.sub(r"\D","", u_raw)
                if not re.fullmatch(r"\d{10}", digits): return "Teléfono inválido. Debe tener 10 dígitos:"
                self.admin.a_phone = digits; self.admin.state = "DIR_ADD_STREET"; return "Calle y número:"
            if s == "DIR_ADD_STREET":
                self.admin.a_street = u_raw.strip()
                if not self.admin.a_street: return "Calle y número, por favor:"
                self.admin.state = "DIR_ADD_CITY"; return "Ciudad/municipio:"
            if s == "DIR_ADD_CITY":
                self.admin.a_city = u_raw.strip()
                if not self.admin.a_city: return "Ciudad/municipio, por favor:"
                self.admin.state = "DIR_ADD_STATE"; return "Estado:"
            if s == "DIR_ADD_STATE":
                self.admin.a_state = u_raw.strip()
                if not self.admin.a_state: return "Estado, por favor:"
                self.admin.state = "DIR_ADD_CP"; return "Código Postal (5 dígitos):"
            if s == "DIR_ADD_CP":
                cp = u_raw.strip()
                if not re.fullmatch(r"\d{5}", cp): return "CP inválido. Debe tener 5 dígitos:"
                self.admin.a_cp = cp
                msg = add_address(self.admin.a_name, self.admin.a_phone, self.admin.a_street, self.admin.a_city, self.admin.a_state, self.admin.a_cp)
                self.admin = AdminCtx(state="DIR_MENU")
                return msg + "\n\n" + address_book_text(load_user()) + "\n\nOpciones: 'agregar', 'elimina 2', 'predeterminada 1', 'atrás' o 'salir'."

        if self.admin.state.startswith("PAGO_"):
            s = self.admin.state
            from amazon_bot.services.user_service import load_user
            if s == "PAGO_MENU":
                if INTENTS["ADD_WORD"].search(u):
                    self.admin.state = "PAGO_ADD_BRAND"; return "Marca de la tarjeta (Visa, MasterCard, American Express, Carnet):"
                m = INTENTS["DEL_IDX"].search(u)
                if m:
                    idx = int(m.group("idx")); msg = delete_card(idx)
                    return msg + "\n\n" + cards_text(load_user()) + "\n\nOpciones: 'agregar', 'elimina 2', 'predeterminado 1', 'atrás' o 'salir'."
                m = INTENTS["SETDEF_IDX"].search(u)
                if m:
                    idx = int(m.group("idx")); msg = set_default_card(idx)
                    return msg + "\n\n" + cards_text(load_user()) + "\n\nOpciones: 'agregar', 'elimina 2', 'predeterminado 1', 'atrás' o 'salir'."
                if INTENTS["ADMIN_DIR_ENTER"].search(u):
                    self.admin.state = "DIR_MENU"
                    return address_book_text(load_user()) + "\n\nOpciones: 'agregar', 'elimina 2', 'predeterminada 1', 'atrás' o 'salir'."
                if INTENTS["ADMIN_PAGO_ENTER"].search(u):
                    return cards_text(load_user()) + "\n\nOpciones: 'agregar', 'elimina 2', 'predeterminado 1', 'atrás' o 'salir'."
                return "¿Qué deseas hacer en métodos de pago? 'agregar', 'elimina 2' o 'predeterminado 1'."
            if s == "PAGO_ADD_BRAND":
                m = INTENTS["BRAND"].search(u)
                if not m: return "Marca no reconocida. Usa: Visa, MasterCard, American Express o Carnet."
                self.admin.c_brand = m.group(1); self.admin.state = "PAGO_ADD_LAST4"; return "Últimos 4 dígitos:"
            if s == "PAGO_ADD_LAST4":
                m = INTENTS["LAST4"].search(u)
                if not m: return "Los últimos 4 dígitos deben ser 4 números:"
                msg = add_card(self.admin.c_brand, m.group(1))
                self.admin = AdminCtx(state="PAGO_MENU")
                return msg + "\n\n" + cards_text(load_user()) + "\n\nOpciones: 'agregar', 'elimina 2', 'predeterminado 1', 'atrás' o 'salir'."

        # ===== 10) Flujo de compras / carrito / categorías =====
        s = self.ctx.state

        # Pagar directo si no hay checkout activo
        if INTENTS["PAY"].search(u):
            msg = checkout(); self.ctx.state = "INICIO"; return msg + "\n\n" + self.prompt()

        # ---- Entrada a CATEGORÍAS por frases naturales ----
        if any(kw in u_norm for kw in ("no se que comprar","no sé que comprar","no se qué comprar","no sé qué comprar","ver categorias","ver categorías","categorias","categorías","muestrame categorias","muéstrame categorías")):
            self.ctx.state = "CATS"; return self.prompt()

        # ---- Navegación de categorías ----
        if s == "CATS":
            # selecciona categoría por número o por nombre
            m = INTENTS.get("SELECT_N") and INTENTS["SELECT_N"].search(u_norm)
            cats = self._all_categories()
            chosen_cat = None
            if m:
                idx = int(m.group("idx"))
                if 1 <= idx <= len(cats): chosen_cat = cats[idx-1]
                else: return "Índice inválido. Elige un número de la lista de categorías."
            else:
                # por nombre
                name = u_raw.strip()
                if name:
                    # match relajado
                    name_norm = normalize(name)
                    chosen_cat = next((c for c in cats if name_norm in normalize(c)), None)
            if not chosen_cat:
                return "No reconocí la categoría. Elige con un número o escribe su nombre tal cual aparece."
            # cargar productos de esa categoría como "last_results"
            results = self._results_from_category(chosen_cat)
            if not results:
                return "No tengo productos en esa categoría por ahora. Prueba con otra."
            self.ctx.last_results = results
            self.ctx.state = "CATS_LISTA"
            lines = [f"Productos en {chosen_cat}:"]
            for i,p in enumerate(results, 1):
                tag = " (tallas)" if int(p.get("has_sizes") or 0) else ""
                lines.append(f"{i}) {p['name']} — ${p['price_cents']/100:.2f}{tag}")
            lines.append("\nElige un número o escribe otra categoría/búsqueda.")
            return "\n".join(lines)

        if s == "CATS_LISTA":
            m = INTENTS["SELECT_N"].search(u_norm)
            if m:
                idx = int(m.group("idx"))
                prod = find_product_by_index(self.ctx.last_results, idx)
                if not prod: return "Índice inválido. Elige un número de la lista."
                self.ctx.current_product = prod; self.ctx.qty = None; self.ctx.size = None
                self.ctx.state = "DETALLE"; return self.prompt()
            # cambiar de categoría / búsqueda libre
            # continúa al bloque de búsqueda general (cae hasta INICIO)

        # ---- Búsqueda general (cuando estamos en INICIO o venimos de CATS_LISTA sin número) ----
        if s in ("INICIO","CATS_LISTA"):
            # Si el texto no disparó otro flujo, trátalo como búsqueda
            self.ctx.last_results = search_products(u_boost)
            if not self.ctx.last_results:
                # Si veníamos de CATS_LISTA, no perdamos el contexto de categorías
                if s == "CATS_LISTA":
                    return "No encontré resultados con esa búsqueda aquí. Elige un número de la lista, otra categoría o escribe otra búsqueda."
                return "No encontré resultados. ¿Probamos con otra palabra o te muestro categorías?"
            self.ctx.state = "LISTA"
            lines = ["Resultados:"]
            for i,p in enumerate(self.ctx.last_results, 1):
                tag = " (tallas)" if int(p.get("has_sizes") or 0) else ""
                lines.append(f"{i}) {p['name']} — ${p['price_cents']/100:.2f}{tag}")
            return "\n".join(lines) + "\n\n" + self.prompt()

        if s == "LISTA":
            m = INTENTS["SELECT_N"].search(u_norm)
            if m:
                idx = int(m.group("idx"))
                prod = find_product_by_index(self.ctx.last_results, idx)
                if not prod: return "Índice inválido. Elige un número de la lista."
                self.ctx.current_product = prod; self.ctx.qty = None; self.ctx.size = None
                self.ctx.state = "DETALLE"; return self.prompt()
            # si escribe otra cosa, tratar como nueva búsqueda
            self.ctx.state = "INICIO"; return self.handle(u_raw)

        if s == "DETALLE":
            p = self.ctx.current_product
            if INTENTS["QTY_ADD"].search(u_boost):
                frag = INTENTS["QTY_ADD"].search(u_boost).group(1); num = parse_qty(frag)
                if num is None: return "No entendí cuánto sumar."
                self.ctx.qty = (self.ctx.qty or 0) + num
            elif INTENTS["QTY_SUB"].search(u_boost):
                frag = INTENTS["QTY_SUB"].search(u_boost).group(1); num = parse_qty(frag)
                if num is None: return "No entendí cuánto quitar."
                self.ctx.qty = max(1, (self.ctx.qty or 1) - num)
            elif INTENTS["QTY_SET"].search(u_boost):
                frag = INTENTS["QTY_SET"].search(u_boost).group(1); num = parse_qty(frag)
                if num is None: return "No entendí la cantidad."
                self.ctx.qty = max(1, num)
            else:
                num = parse_qty(u_boost)
                if num: self.ctx.qty = max(1, num)

            sz = parse_size(u_boost)
            if sz: self.ctx.size = sz

            if int(p.get("has_sizes") or 0) and not self.ctx.size:
                return "Este producto requiere talla (XS,S,M,L,XL,XXL). Dime la talla (ej. 'talla M')."
            if not self.ctx.qty:
                return "¿Cuántas piezas quieres? (ej. 'pon 2', 'par', 'docena')"
            if not stock_available(p["product_id"], self.ctx.size, self.ctx.qty):
                return "No hay stock suficiente. Probemos con menos cantidad o otra talla."

            self.ctx.state = "CONFIRMAR"; return self.prompt()

        if s == "CONFIRMAR":
            if INTENTS["CONFIRM"].search(u_boost):
                ok, msg = cart_add(self.ctx.current_product["product_id"], self.ctx.qty, self.ctx.size)
                self.ctx.state = "CARRITO" if ok else "DETALLE"
                return msg + ("\n\n" + self.prompt() if ok else "")
            if INTENTS["DENY"].search(u_boost):
                self.ctx.state = "DETALLE"; return "Sin problema, dime otra cantidad/talla. 🙂"
            self.ctx.state = "DETALLE"; return self.handle(u_raw)

        if s == "CARRITO":
            # Natural language operaciones por nombre de producto
            # "quiero una playera más", "quita dos calcetines", "cambia la sudadera a 3", "elimina los tenis"
            # 1) Vaciar / pagar / seguir buscando
            if "vaciar" in u_norm:
                msg = cart_clear(); return msg + "\n\n" + self.prompt()
            if "pagar" in u_norm:
                from amazon_bot.services.cart_service import load_cart
                if load_cart()["items"]:
                    return self._enter_checkout_review()
                return checkout() + "\n\n" + self.prompt()
            if "buscar" in u_norm or "seguir" in u_norm:
                self.ctx.state = "INICIO"; return self.prompt()

            # 2) Comandos clásicos por índice
            m = INTENTS["CART_REMOVE_INDEX"].search(u_boost)
            if m:
                idx = int(m.group("idx")); msg = cart_remove_index(idx); return msg + "\n\n" + self.prompt()
            m = INTENTS["CART_SET_QTY_IDX"].search(u_boost)
            if m:
                idx = int(m.group("idx")); qtxt = m.group("qty_text"); qty = parse_qty(qtxt)
                if qty is None: return "No entendí la cantidad. Ej: 'cambia cantidad del 1 a 3'."
                msg = cart_set_qty_index(idx, qty); return msg + "\n\n" + self.prompt()
            m = INTENTS["CART_ADD_QTY_IDX"].search(u_boost)
            if m:
                idx = int(m.group("idx")); qtxt = m.group("qty_text"); qty = parse_qty(qtxt)
                if qty is None: return "No entendí cuánto sumar. Ej: 'suma 2 al 1'."
                msg = cart_add_qty_index(idx, qty); return msg + "\n\n" + self.prompt()
            m = INTENTS["CART_SUB_QTY_IDX"].search(u_boost)
            if m:
                idx = int(m.group("idx")); qtxt = m.group("qty_text"); qty = parse_qty(qtxt)
                if qty is None: return "No entendí cuánto quitar. Ej: 'quita 1 al 2'."
                msg = cart_sub_qty_index(idx, qty); return msg + "\n\n" + self.prompt()

            # 3) Natural por NOMBRE
            # Detectar verbos clave
            add_more = any(w in u_norm for w in ("mas","más","agrega","añade","sumar","suma"))
            sub_less = any(w in u_norm for w in ("quita","remueve","resta","menos"))
            set_to   = any(w in u_norm for w in ("pon","deja en","cámbia a","cambia a","cambiar a","dejar a"))
            delete_p = any(w in u_norm for w in ("elimina","borra","quitar"))

            # Intentar detectar un número y un nombre
            qty = parse_qty(u_boost) or (1 if (add_more or sub_less) else None)
            # Producto: buscar última palabra >3 chars que aparezca en el carrito
            tokens = [t for t in re.split(r"[^\wáéíóúñü]+", u_raw) if len(t.strip()) >= 3]
            idx_name = None
            for t in tokens:
                idx_name = self._find_cart_index_by_name(t)
                if idx_name: break

            if idx_name:
                if delete_p:
                    msg = cart_remove_index(idx_name); return msg + "\n\n" + self.prompt()
                if add_more and qty:
                    msg = cart_add_qty_index(idx_name, qty); return msg + "\n\n" + self.prompt()
                if sub_less and qty:
                    msg = cart_sub_qty_index(idx_name, qty); return msg + "\n\n" + self.prompt()
                if set_to and qty:
                    msg = cart_set_qty_index(idx_name, qty); return msg + "\n\n" + self.prompt()

            # Si nada hizo match, deja el prompt tal cual
            return self.prompt()

        # ===== 12) Fallback =====
        self.ctx.state = "INICIO"; return self.prompt()