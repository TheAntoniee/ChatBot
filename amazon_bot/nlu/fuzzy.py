# amazon_bot/nlu/fuzzy.py
import re
import unicodedata

def _strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')

def _squash_repeats(s: str) -> str:
    # colapsa repeticiones largas: holaaaa -> holaa
    return re.sub(r'(.)\1{2,}', r'\1\1', s)

# Patrones "amplios" (permiten letras de más/menos y variantes comunes)
# Nota: trabajamos sobre texto ya en minúsculas y sin tildes (tu normalize ya ayuda).
PATTERNS = {
    # Intención de BUSCAR/COMPRAR (dispara SEARCH por "quiero"/"comprar"/"buscar")
    "quiero": re.compile(r"\b(k+i*e*r*o+|q+u*i*e*r*o+|q+r*o+|k+r*o+)\b"),
    "comprar": re.compile(r"\b(c+o*m*p*r*a*r+|co?m?pr+a+r+|com+pr+a*r+|comr+ar+|com+o?rar+|cam+prar+)\b"),
    "buscar":  re.compile(r"\b(b+u*s*c+a*r+|b+u+sca+r+|b+u+sk+a*r+|b+u+car+|b+sc+a+r+)\b"),

    # Otras intenciones claves
    "pagar":   re.compile(r"\b(p+ag+a*r+|pag+ar+|p+g+r+|pag+o+|checkout)\b"),
    "carrito": re.compile(r"\b(c+ar+ri+t+o+|car+it+o+|car+ro)\b"),
    "devolver":re.compile(r"\b(de+vo+l+v+e*r+|devol+e*r|de+v+o+lu+c+i+o*n)\b"),
    "reembolso": re.compile(r"\b(re+e+mb+ol+s*o+|re+em+b+ol+so)\b"),
    "pedidos": re.compile(r"\b(p+e+di+d+o+s+|mis\s+p+e+di+d+o+s+|ordi+nes)\b"),
    "direcciones": re.compile(r"\b(di+re+cc?i+o+n+e*s?|do+mi+ci+li+o+s?)\b"),
    "pagos": re.compile(r"\b(pa+g+o+s?|tar+je+t+a+s?)\b"),
    "rastrear": re.compile(r"\b(r+as+tr+e+a*r+|tr+ac+k|tr+ac+ki+ng|se+gui+mi+e+nt+o)\b"),
}

# Qué palabra canónica le “inyectamos” si detectamos la variante
CANONICAL_TOKENS = {
    "quiero": "quiero",
    "comprar": "comprar",
    "buscar": "buscar",
    "pagar": "pagar",
    "carrito": "carrito",
    "devolver": "devolver",
    "reembolso": "reembolso",
    "pedidos": "pedidos",
    "direcciones": "direcciones",
    "pagos": "pagos",
    "rastrear": "rastrear",
}

def fuzzy_boost(text: str) -> str:
    """
    Devuelve el texto original + (si aplica) tokens canónicos agregados al final.
    No destruye lo que escribió el usuario, sólo 'inyecta' palabras canónicas.
    Ej: 'kro comorar algoo' -> 'kro comorar algoo comprar'
    """
    if not text:
        return text

    # Normalizamos de forma ligera; tu normalize() ya hace otras cosas:
    base = _strip_accents(text.lower())
    base = _squash_repeats(base)

    augmented = text
    already = " " + base + " "  # bordes para no duplicar si ya existe

    for key, rx in PATTERNS.items():
        if rx.search(base):
            canon = CANONICAL_TOKENS[key]
            # si ya está la palabra canónica, no la duplicamos
            if f" {canon} " not in already:
                augmented = f"{augmented} {canon}"
                already += f"{canon} "

    return augmented