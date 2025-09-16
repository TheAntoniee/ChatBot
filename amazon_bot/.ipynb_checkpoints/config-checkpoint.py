# Ventanas/políticas demo
CANCEL_WINDOW_MIN = 30          # cancelar sin enviar, en minutos
RETURN_WINDOW_DAYS = 30         # días para devolución

# Carpetas
DATA_DIR = "data"
STATE_DIR = "state"

# Rutas CSV/JSON (persistencia simple)
PRODUCTS_CSV        = f"{DATA_DIR}/products.csv"
VARIANTS_CSV        = f"{DATA_DIR}/product_variants.csv"
ORDERS_CSV          = f"{DATA_DIR}/orders.csv"
ORDER_ITEMS_CSV     = f"{DATA_DIR}/order_items.csv"
RETURNS_CSV         = f"{DATA_DIR}/returns.csv"
REFUNDS_CSV         = f"{DATA_DIR}/refunds.csv"
SHIPMENTS_CSV       = f"{DATA_DIR}/shipments.csv"  # NUEVO: rastreo

USER_JSON           = f"{STATE_DIR}/user.json"
CART_JSON           = f"{STATE_DIR}/cart.json"