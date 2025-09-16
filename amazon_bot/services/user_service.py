import re
from typing import Any, Dict, List, Optional
from amazon_bot.utils.io_utils import read_json, write_json
from amazon_bot.config import USER_JSON
from amazon_bot.utils.text_utils import normalize

def load_user() -> Dict[str, Any]:
    return read_json(USER_JSON, {"user_id": 1, "addresses": [], "payment_methods": []})

def save_user(u: Dict[str, Any]):
    write_json(USER_JSON, u)

def address_book_text(u: Dict[str, Any]) -> str:
    if not u["addresses"]:
        return "No tienes direcciones guardadas."
    lines = ["Direcciones:"]
    for i, a in enumerate(u["addresses"], 1):
        tag = " (predeterminada)" if a.get("is_default") else ""
        lines.append(f"{i}) {a['name']} — {a['street']}, {a['city']}, {a['state']}, CP {a['postal_code']} — {a['phone']}{tag}")
    return "\n".join(lines)

def cards_text(u: Dict[str, Any]) -> str:
    if not u["payment_methods"]:
        return "No tienes métodos de pago guardados."
    lines = ["Métodos de pago:"]
    for i, pm in enumerate(u["payment_methods"], 1):
        tag = " (predeterminado)" if pm.get("is_default") else ""
        brand = pm.get("brand","").upper()
        lines.append(f"{i}) {brand} ••{pm['last4']}{tag}")
    return "\n".join(lines)

def set_default_address(idx: int) -> str:
    u = load_user()
    if not (1 <= idx <= len(u["addresses"])): return "Índice inválido."
    for a in u["addresses"]: a["is_default"] = False
    u["addresses"][idx-1]["is_default"] = True
    save_user(u); return "Dirección marcada como predeterminada."

def delete_address(idx: int) -> str:
    u = load_user()
    if not (1 <= idx <= len(u["addresses"])): return "Índice inválido."
    removed = u["addresses"].pop(idx-1)
    if removed.get("is_default") and u["addresses"]:
        u["addresses"][0]["is_default"] = True
    save_user(u); return "Dirección eliminada."

def add_address(name:str, phone:str, street:str, city:str, state_s:str, postal:str) -> str:
    if not re.fullmatch(r"\d{10}", re.sub(r"\D", "", phone or "")): return "Teléfono inválido (10 dígitos)."
    if not re.fullmatch(r"\d{5}", postal or ""): return "CP inválido (5 dígitos)."
    u = load_user()
    next_id = (max([a["id"] for a in u["addresses"]] or [0]) + 1)
    is_default = not any(a.get("is_default") for a in u["addresses"])
    u["addresses"].append({
        "id": next_id, "name": name, "phone": re.sub(r"\D","",phone),
        "street": street, "city": city, "state": state_s, "postal_code": postal,
        "is_default": is_default
    })
    save_user(u); return "Dirección agregada."

def set_default_card(idx: int) -> str:
    u = load_user()
    if not (1 <= idx <= len(u["payment_methods"])): return "Índice inválido."
    for p in u["payment_methods"]: p["is_default"] = False
    u["payment_methods"][idx-1]["is_default"] = True
    save_user(u); return "Método de pago predeterminado actualizado."

def delete_card(idx: int) -> str:
    u = load_user()
    if not (1 <= idx <= len(u["payment_methods"])): return "Índice inválido."
    removed = u["payment_methods"].pop(idx-1)
    if removed.get("is_default") and u["payment_methods"]:
        u["payment_methods"][0]["is_default"] = True
    save_user(u); return "Método de pago eliminado."

def add_card(brand:str, last4:str) -> str:
    brand = normalize(brand)
    brand_map = {
        "visa":"visa", "mastercard":"mastercard", "master card":"mastercard",
        "american express":"american express", "amex":"american express", "carnet":"carnet"
    }
    found = None
    for k,v in brand_map.items():
        if k in brand: found = v; break
    if not found: return "Marca no reconocida. Usa: Visa, MasterCard, American Express o Carnet."
    if not re.fullmatch(r"\d{4}", last4 or ""): return "Los últimos 4 dígitos deben ser 4 números."
    u = load_user()
    next_id = (max([p["id"] for p in u["payment_methods"]] or [0]) + 1)
    is_default = not any(p.get("is_default") for p in u["payment_methods"])
    u["payment_methods"].append({"id":next_id, "brand":found, "last4":last4, "token":f"tok_{found}_{last4}", "is_default":is_default})
    save_user(u); return "Método de pago agregado."

def default_address() -> Optional[Dict[str, Any]]:
    u = load_user()
    if not u["addresses"]: return None
    for a in u["addresses"]:
        if a.get("is_default"): return a
    return u["addresses"][0]

def list_cards() -> List[Dict[str, Any]]:
    return load_user().get("payment_methods", [])

def format_address_line(a: Dict[str, Any]) -> str:
    return f"{a['name']} — {a['street']}, {a['city']}, {a['state']}, CP {a['postal_code']} — {a['phone']}"

def get_display_name() -> Optional[str]:
    """
    Devuelve el nombre corto del usuario.
    Prioridad:
      1) user.profile.first_name
      2) nombre de la dirección predeterminada (primer token)
      3) nombre de la primera dirección (primer token)
    """
    u = load_user()
    # 1) perfil
    prof = u.get("profile") or {}
    first = (prof.get("first_name") or "").strip()
    if first:
        return first

    # 2) dirección predeterminada
    addrs = u.get("addresses", [])
    pref = next((a for a in addrs if a.get("is_default")), None)
    cand = (pref or (addrs[0] if addrs else {})).get("name") or ""
    cand = cand.strip()
    if cand:
        return re.split(r"\s+", cand)[0].title()

    return None


def set_display_name(name: str) -> str:
    """
    Guarda el nombre corto en user.profile.first_name
    """
    name = (name or "").strip()
    if not name:
        return "Dime tu nombre, por fa."
    first = re.split(r"\s+", name)[0].title()

    u = load_user()
    prof = u.get("profile") or {}
    prof["first_name"] = first
    u["profile"] = prof
    save_user(u)
    return f"¡Mucho gusto, {first}!"

