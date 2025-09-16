def ok(msg: str) -> str:
    return f"✅ {msg}"

def warn(msg: str) -> str:
    return f"⚠ {msg}"

def err(msg: str) -> str:
    return f"❌ {msg}"

def friendly_greeting() -> str:
    return ("¡Hola! 👋 Estoy para ayudarte con tus compras, envíos, devoluciones, reembolsos "
            "y la administración de tus direcciones y métodos de pago. ¿Qué te gustaría hacer?")

def quick_options() -> str:
    return ("Puedes decir: buscar, ver carrito, pagar, mis pedidos, devolver, "
            "reembolso, rastrear, direcciones, pagos, cancelar pedido o salir.")