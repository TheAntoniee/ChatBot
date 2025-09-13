# Gestión de cuenta y seguridad
# Amazon Prime y suscripciones
# Soporte técnico de dispositivos

import re
import time
import random
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

#Expresiones regulares generales
email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
telefono_regex = r'^\+?[0-9]{7,15}$'
nombre_regex = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$'

# Expresiones regulares
Gestion_Cuenta_RE = r"""(?i)\b((no\s+)?(puedo|puede|podr[ií]a)\s+(acceder|entrar|ingresar|iniciar|acceso)|(a|la|mi)|(olvid[ée]|perd[ií]|recuperar|restablecer|resetear|Cambiar)\s+(contrase[ñn]a|password|clave|acceso)|(verificaci[óo]n|autenticaci[óo]n|2fa|doble\s+factor|c[óo]digo)\s+(dos\s+pasos|seguridad)|(bloqueo|bloqueada|suspendida)\s+cuenta|cuenta\s+(bloqueo|bloqueada|suspendida)|(dispositivo|sesi[óo]n)\s+(conectado|activa|abierta|no\s+reconocido)|(alert|notificaci[óo]n|alerta)\s+seguridad|seguridad\s+(alert|notificaci[óo]n|alerta)|(activ|desactiv|configur)\s+(seguridad|verificaci[óo]n|notificaci[óo]n)|(cambiar|actualizar|modificar)\s+(correo|email|tel[ée]fono|n[úu]mero|direcci[óo]n)|(datos|informaci[óo]n)\s+personal|personal\s+(datos|informaci[óo]n)|(eliminar|cerrar|borrar)\s+cuenta|cuenta\s+(eliminar|cerrar|borrar)|(problema|error|dificultad|duda)\s+(sesi[óo]n|login|acceso|cuenta))\b"""
Prime_Suscripciones_RE = r"(?i)\b(prime|suscripción|membresía|anual|mensual|gratis|prueba|renovación|cancelar|reactivar|beneficios|envío gratis|prime video|prime music|prime gaming|prime reading|kindle unlimited|amazon music|amazon video|amazon photos|almacenamiento ilimitado|oferta|descuento|promoción|factura|recibo|pago|método de pago|día prime|prime day|devolución|reembolso|garantía)\b"
Soporte_Tecnico_RE = r"(?i)\b(dispositivo|kindle|fire tv|echo|alexa|fire tablet|fire stick|ring|blink|setup|configurar|conectar|wifi|bluetooth|actualización|firmware|software|hardware|pantalla|batería|carga|encender|apagar|reiniciar|resetear|restablecer fábrica|problema|error|fallo|no funciona|lento|congelado|térmico|sobrecalentamiento|garantía|reparación|reemplazo|troubleshooting|solución|guía|manual|instrucciones|compatibilidad|drivers|controladores)\b"

# Función para clasificar la consulta
def clasificar_consulta(texto):
    if re.search(Gestion_Cuenta_RE, texto):
        return Categoria.GESTION_CUENTA
    elif re.search(Prime_Suscripciones_RE, texto):
        return Categoria.PRIME_SUSCRIPCIONES
    elif re.search(Soporte_Tecnico_RE, texto):
        return Categoria.SOPORTE_TECNICO
    else:
        return Categoria.NO_RECONOCIDO

# Respuestas específicas por categoría
respuestas = {
    Categoria.GESTION_CUENTA: [
        "Para recuperar tu contraseña, visita la página de recuperación de cuenta: https://www.amazon.com/ap/forgotpassword",
        "Si tu cuenta está bloqueada, por favor contacta con el soporte de Amazon: https://www.amazon.com/gp/help/customer/contact-us",
    ],
    Categoria.PRIME_SUSCRIPCIONES: [

    ],
    Categoria.SOPORTE_TECNICO: [
        
    ]
}

state = 0
salida = True
categoria_actual = None

# Flujo de conversación
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
            user_input = input("¿Podrías proporcionar más detalles sobre tu problema?")
            
            if categoria_actual in respuestas:
                print("Te sugiero:")
                for respuesta in respuestas[categoria_actual]:
                    print(f"- {respuesta}")
                
            else:
                print("Lo siento, no tengo información específica para tu consulta. ¿Quieres intentar con otra consulta?")
                salida = False  

    except KeyboardInterrupt:
        print("\nGracias por usar el chatbot de Amazon. ¡Hasta pronto!")
        break