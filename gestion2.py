import re
import time
import random
import csv
import os
from enum import Enum

class Categoria(Enum):
    GESTION_CUENTA = 1
    PRIME_SUSCRIPCIONES = 2
    SOPORTE_TECNICO = 3
    NO_RECONOCIDO = 4

despedidas = [
    "Adiós",
    "Hasta luego",
    "Que tenga un buen día",
    "Nos vemos pronto",
    "Gracias por contactar"
]

# ---------------------------
# Expresiones regulares
# ---------------------------
email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
telefono_regex = r'^\+?[0-9]{7,15}$'
nombre_regex = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$'
tarjeta_regex = r'^\d{16}$'
direccion_regex = r'^[\w\s\#\-\.,áéíóúÁÉÍÓÚñÑ]+$'

Gestion_Cuenta_RE = r"""(?i)\b((no\s+)?(puedo|puede|podr[ií]a)\s+(acceder|entrar|ingresar|iniciar|acceso)|(olvid[ée]|perd[ií]|recuperar|restablecer|resetear|cambiar)\s+(contrase[ñn]a|password|clave|acceso)|(verificaci[óo]n|autenticaci[óo]n|2fa|doble\s+factor|c[óo]digo)\s+(dos\s+pasos|seguridad)|(bloqueo|bloqueada|suspendida)\s+cuenta|(cambiar|actualizar|modificar)\s+(correo|email|tel[ée]fono|n[úu]mero|direcci[óo]n)|(eliminar|cerrar|borrar)\s+cuenta|(problema|error|dificultad|duda)\s+(sesi[óo]n|login|acceso|cuenta))\b"""
Prime_Suscripciones_RE = r"(?i)\b(prime|suscripci[óo]n|membres[ií]a|anual|mensual|gratis|prueba|renovaci[óo]n|cancelar|reactivar|beneficios|env[ií]o gratis|prime video|prime music|prime gaming|prime reading|kindle unlimited|amazon music|amazon video|amazon photos|almacenamiento ilimitado|oferta|descuento|promoci[óo]n|factura|recibo|pago|m[ée]todo de pago|d[ií]a prime|prime day|devoluci[óo]n|reembolso|garant[ií]a)\b"
Soporte_Tecnico_RE = r"(?i)\b(dispositivo|kindle|fire tv|echo|alexa|fire tablet|fire stick|ring|blink|setup|configurar|conectar|wifi|bluetooth|actualizaci[óo]n|firmware|software|hardware|pantalla|bater[ií]a|carga|encender|apagar|reiniciar|resetear|restablecer f[áa]brica|problema|error|fallo|no funciona|lento|congelado|sobrecalentamiento|garant[ií]a|reparaci[óo]n|reemplazo|troubleshooting|manual|instrucciones|compatibilidad|drivers|controladores)\b"

# ---------------------------
# Clasificación
# ---------------------------
def clasificar_consulta(texto):
    if re.search(Gestion_Cuenta_RE, texto):
        return Categoria.GESTION_CUENTA
    elif re.search(Prime_Suscripciones_RE, texto):
        return Categoria.PRIME_SUSCRIPCIONES
    elif re.search(Soporte_Tecnico_RE, texto):
        return Categoria.SOPORTE_TECNICO
    else:
        return Categoria.NO_RECONOCIDO

# ---------------------------
# Respuestas
# ---------------------------
respuestas = {
    Categoria.GESTION_CUENTA: [
        "Para recuperar tu contraseña, visita: https://www.amazon.com/ap/forgotpassword",
        "Si tu cuenta está bloqueada, contacta soporte: https://www.amazon.com/gp/help/customer/contact-us",
        "Puedes actualizar tu correo o teléfono desde 'Login y seguridad': https://www.amazon.com/hz/account-information",
        "Si detectaste un inicio de sesión no reconocido, revisa actividad reciente aquí: https://www.amazon.com/hz/mycd",
        "Activa verificación en dos pasos siguiendo esta guía: https://www.amazon.com/gp/help/customer/display.html?nodeId=G6JDRWJ5PKWKG7FR",
        "Para cerrar tu cuenta permanentemente: https://www.amazon.com/gp/help/customer/display.html?nodeId=GDKRQFGKPH8G8YFR"
    ],
    Categoria.PRIME_SUSCRIPCIONES: [
        "Administra tu suscripción Prime aquí: https://www.amazon.com/prime",
        "Para cancelar tu membresía Prime: https://www.amazon.com/gp/primecentral",
        "Activa tu prueba gratuita aquí: https://www.amazon.com/tryprimefree",
        "Consulta beneficios de Prime Video: https://www.primevideo.com",
        "Solicita un reembolso de Prime aquí: https://www.amazon.com/gp/help/customer/display.html?nodeId=GVPDF46GWEPWZ2SV",
        "Prime incluye Prime Music y Prime Reading sin costo adicional.",
        "En el Prime Day hay ofertas exclusivas para miembros."
    ],
    Categoria.SOPORTE_TECNICO: [
        "Configura tu Kindle con esta guía: https://www.amazon.com/gp/help/customer/display.html?nodeId=200529680",
        "Si tu Fire TV no enciende, reinícialo desconectándolo 30 segundos.",
        "Actualiza el software de tu Echo desde la app de Alexa.",
        "Problemas de Wi-Fi en dispositivos: https://www.amazon.com/gp/help/customer/display.html?nodeId=201452680",
        "Restablecer Fire Tablet a fábrica: botón encendido + volumen.",
        "Si tu batería no carga, usa cargador original Amazon.",
        "Consulta compatibilidad de dispositivos aquí: https://www.amazon.com/gp/help/customer/display.html?nodeId=201994850",
        "Solicita un reemplazo en garantía: https://www.amazon.com/returns"
    ]
}

# ---------------------------
# CSV helpers
# ---------------------------
def inicializar_csv():
    if not os.path.exists("suscripciones.csv"):
        with open("suscripciones.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["email", "estado"])
            writer.writerow(["cruzalan04@gmail.com", "activo"])
            writer.writerow(["jesusmart12@gmail.com", "activo"])
            writer.writerow(["mariahern3@gmail.com", "cancelado"])

def buscar_suscripcion(email):
    with open("suscripciones.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["email"].lower() == email.lower():
                return row["estado"]
    return None

def cancelar_suscripcion(email):
    filas = []
    encontrado = False
    with open("suscripciones.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["email"].lower() == email.lower():
                row["estado"] = "cancelado"
                encontrado = True
            filas.append(row)
    if encontrado:
        with open("suscripciones.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["email", "estado"])
            writer.writeheader()
            writer.writerows(filas)
    return encontrado

# ---------------------------
# Flujo chatbot
# ---------------------------
state = 0
salida = True
categoria_actual = None

inicializar_csv()

print("Hola, soy el Chatbot de Amazon. ¿En qué puedo ayudarte hoy?")

while salida:
    try:
        if state == 0:
            time.sleep(1)
            user_input = input("Por favor, describe tu consulta: ")
            
            categoria_actual = clasificar_consulta(user_input)
            
            if categoria_actual != Categoria.NO_RECONOCIDO:
                state = 1
                print(f"Entiendo que tienes una consulta sobre {categoria_actual.name.replace('_', ' ').title()}.")
            else:
                print("Lo siento, no he entendido tu consulta. ¿Podrías reformularla?")
                continue
        
        elif state == 1:
            time.sleep(1)
            if categoria_actual == Categoria.PRIME_SUSCRIPCIONES:
                email = input("Por favor, dame el correo asociado a tu suscripción Prime: ")
                if re.match(email_regex, email):
                    estado = buscar_suscripcion(email)
                    if estado is None:
                        print("No encontré ninguna suscripción con ese correo.")
                    elif estado == "cancelado":
                        print("Tu suscripción ya está cancelada.")
                    else:
                        opcion = input("¿Quieres cancelar tu suscripción? (sí/no): ")
                        if opcion.lower() in ["si", "sí", "yes", "y"]:
                            if cancelar_suscripcion(email):
                                print("Tu suscripción ha sido cancelada exitosamente.")
                            else:
                                print("Ocurrió un error al cancelar la suscripción.")
                        else:
                            print("Tu suscripción sigue activa. ")
                else:
                    print("El formato del correo no es válido.")
            
            if categoria_actual in respuestas:
                print("\nTe sugiero:")
                for respuesta in respuestas[categoria_actual]:
                    print(f"- {respuesta}")
                
            else:
                print("Lo siento, no tengo información específica para tu consulta. ¿Quieres intentar con otra consulta?")
                salida = False  

    except KeyboardInterrupt:
        print("\nGracias por usar el chatbot de Amazon. ¡Hasta pronto!")
        break
