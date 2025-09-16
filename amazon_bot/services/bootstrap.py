import csv, os
from amazon_bot.config import PRODUCTS_CSV, VARIANTS_CSV, ORDERS_CSV, ORDER_ITEMS_CSV, RETURNS_CSV, REFUNDS_CSV, USER_JSON, CART_JSON, SHIPMENTS_CSV
from amazon_bot.utils.io_utils import ensure_dirs, read_json, write_json

def bootstrap():
    ensure_dirs()
    if not os.path.exists(PRODUCTS_CSV):
        with open(PRODUCTS_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["product_id","name","category","price_cents","has_sizes","stock"])
            w.writerow([1,"Playera básica unisex","ropa",19900,1,""])
            w.writerow([2,"Sudadera con gorro","ropa",59900,1,""])
            w.writerow([3,"Cafetera goteo 12 tazas","hogar",149900,0,15])
    if not os.path.exists(VARIANTS_CSV):
        with open(VARIANTS_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["variant_id","product_id","size","stock"])
            w.writerow([101,1,"s",12]); w.writerow([102,1,"m",8]); w.writerow([103,1,"l",5])
            w.writerow([201,2,"m",6]); w.writerow([202,2,"l",4]); w.writerow([203,2,"xl",3])
    if not os.path.exists(ORDERS_CSV):
        with open(ORDERS_CSV, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["order_number","status","subtotal_cents","shipping_cents","total_cents","created_at"])
    if not os.path.exists(ORDER_ITEMS_CSV):
        with open(ORDER_ITEMS_CSV, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["order_number","product_id","variant_id","size","qty","unit_price_cents"])
    if not os.path.exists(RETURNS_CSV):
        with open(RETURNS_CSV, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["return_id","order_number","item_idx","product_id","variant_id","size","qty","reason","method","status","created_at"])
    if not os.path.exists(REFUNDS_CSV):
        with open(REFUNDS_CSV, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["refund_id","order_number","amount_cents","status","processed_at"])
    if not os.path.exists(SHIPMENTS_CSV):
        with open(SHIPMENTS_CSV, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(["order_number","tracking_number","carrier","created_at"])
    _ = read_json(USER_JSON, {
        "user_id": 1,
        "addresses": [{
            "id": 1, "name": "Usuario Demo", "phone": "5512345678",
            "street": "Calle Falsa 123", "city": "CDMX", "state": "CDMX", "postal_code": "06000",
            "is_default": True
        }],
        "payment_methods": [{
            "id": 1, "brand": "visa", "last4": "4242", "token": "tok_demo", "is_default": True
        }]
    })
    _ = read_json(CART_JSON, {"items": []})