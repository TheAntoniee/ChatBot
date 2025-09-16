import re, unicodedata, random

def normalize(text: str) -> str:
    t = text.strip().lower()
    t = ''.join(c for c in unicodedata.normalize('NFKD', t) if not unicodedata.combining(c))
    t = re.sub(r'(.)\1{2,}', r'\1\1', t)           # "siiiii" -> "sii"
    t = re.sub(r'[\u263a-\U0001f645]+', ' ', t)    # emojis comunes
    t = re.sub(r'\s+', ' ', t)
    return t

def gen_order_number() -> str:
    a = f"{random.randint(100,999)}"
    b = f"{random.randint(0,9999999):07d}"
    c = f"{random.randint(0,9999999):07d}"
    return f"{a}-{b}-{c}"