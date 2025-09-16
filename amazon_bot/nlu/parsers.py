import re
from typing import Optional
from amazon_bot.utils.text_utils import normalize

WORDS = {
   "cero":0,"un":1,"una":1,"uno":1,"dos":2,"tres":3,"cuatro":4,"cinco":5,"seis":6,
   "siete":7,"ocho":8,"nueve":9,"diez":10,"once":11,"doce":12
}
ESPECIALES = {"par":2, "media docena":6, "docena":12}
RE_NUM = re.compile(r"(?P<num>\d+)")
RE_ESP = re.compile(r"(media docena|docena|par)")
RE_PAL = re.compile("|".join(sorted(map(re.escape, WORDS.keys()), key=len, reverse=True)))

TALLA_EQ = {"extra chica":"xs","chica":"s","ch":"s","mediana":"m","med":"m","grande":"l","extra grande":"xl"}
RE_TALLA = re.compile(r"(?:talla\s*)?(?P<talla>xs|s|m|l|xl|xxl|extrachica|chica|ch|mediana|med|grande|extra grande)\b")

def parse_qty(fragment: str) -> Optional[int]:
    frag = normalize(fragment)
    m = RE_NUM.search(frag)
    if m: return int(m.group("num"))
    m = RE_ESP.search(frag)
    if m: return ESPECIALES[m.group(1)]
    m = RE_PAL.search(frag)
    if m: return WORDS[m.group(0)]
    return None

def parse_size(text: str) -> Optional[str]:
    t = normalize(text)
    m = RE_TALLA.search(t)
    if not m: return None
    raw = m.group("talla")
    return TALLA_EQ.get(raw, raw)