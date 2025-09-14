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

Gestion_Cuenta_RE = re.compile(r"""
    (?ix)       
    \b(?:
        # Problemas de acceso
        (?P<acceso>(?:no\s+)?(?:pued[oe]|podr[ií]a)\s+(?:acceder|entrar|ingresar|iniciar|acceso))
        # Contraseñas
        |(?P<contrasena>(?:olvid[ée]|perd[ií]|recuperar|restablecer|resetear|cambiar)\s+)
        |(?P<pronombres>(?:mi|mis|tu|tus|su|sus|nuestro|nuestra|nuestros|nuestras)\s+)
        |(?P<acceso2>(?:contraseña|password|clave|pin|código|codigo)\s+)
        # Verificación en dos pasos
        |(?P<verificacion>(?:verificaci[óo]n|autenticaci[óo]n|2fa|doble\s+factor|c[óo]digo)\s+(?:dos\s+pasos|seguridad))
        # Cuenta bloqueada
        |(?P<bloqueo>(?:bloque[ao]|bloqueada|suspendida)\s+cuenta|cuenta\s+(?:bloque[ao]|bloqueada|suspendida))
        # Dispositivos y sesiones
        |(?P<sesion>(?:dispositivo|sesi[óo]n)\s+(?:(?:no\s+)?reconocido|conectad[ao]|activ[ao]|abierta))
        # Alertas de seguridad
        |(?P<alerta>(?:alert|notificaci[óo]n|alerta)\s+seguridad|seguridad\s+(?:alert|notificaci[óo]n|alerta))
        # Configuración de seguridad
        (?P<configuracion>(?:activ|desactiv|configur)\s+(?:seguridad|verificaci[óo]n|notificaci[óo]n))
        # Cambio de datos de contacto
        |(?P<contacto>(?:cambiar|actualizar|modificar)\s+(?:correo|email|tel[ée]fono|n[úu]mero|direcci[óo]n))
        # Datos personales
        |(?P<datos>(?:datos|informaci[óo]n)\s+personal|personal\s+(?:datos|informaci[óo]n))
        # Eliminación de cuenta
        |(?P<eliminar>(?:eliminar|cerrar|borrar)\s+cuenta|cuenta\s+(?:eliminar|cerrar|borrar))
        # Problemas generales
        |(?P<problema>(?:problema|error|dificultad|duda)\s+(?:sesi[óo]n|login|acceso|cuenta))
                              
    )\b
""", re.VERBOSE)
Prime_Suscripciones_RE = re.compile(r"""
    (?ix)
    \b(?:
        # Suscripciones y membresías
        (?P<suscripcion>(?:prime|suscripción|membresía|anual|mensual|gratis|prueba|renovación|cancelar|reactivar|beneficios|envío gratis|prime video|prime music|prime gaming|prime reading|kindle unlimited|amazon music|amazon video|amazon photos|almacenamiento ilimitado|oferta|descuento|promoción|factura|recibo|pago|método de pago|día prime|prime day|devolución|reembolso|garantía))
    )\b
""", re.VERBOSE)
Soporte_Tecnico_RE = re.compile(r"""
    (?ix)
    \b(?:
        # Soporte técnico
        (?P<soporte>(?:dispositivo|kindle|fire tv|echo|alexa|fire tablet|fire stick|ring|blink|setup|configurar|conectar|wifi|bluetooth|actualización|firmware|software|hardware|pantalla|batería|carga|encender|apagar|reiniciar|resetear|restablecer fábrica|problema|error|fallo|no funciona|lento|congelado|térmico|sobrecalentamiento|garantía|reparación|reemplazo|troubleshooting|solución|guía|manual|instrucciones|compatibilidad|drivers|controladores))
    )\b
""", re.VERBOSE)
no_RE = re.compile(r'^(?:no|n|no,?\s+gracias)$', re.IGNORECASE)
si_RE = re.compile(r'^(?:s[ií]|s|claro|por\s+supuesto)$', re.IGNORECASE)

# Función para clasificar la consulta
def clasificar_consulta(texto):
    match = Gestion_Cuenta_RE.search(texto)
    if match:
        return Categoria.GESTION_CUENTA, match
    match = Prime_Suscripciones_RE.search(texto)
    if match:
        return Categoria.PRIME_SUSCRIPCIONES, match
    match = Soporte_Tecnico_RE.search(texto)
    if match:
        return Categoria.SOPORTE_TECNICO, match
    return Categoria.NO_RECONOCIDO, None

def manejar_acceso(match_obj):
    print("Problema de acceso")
    texto = match_obj.group('acceso')
    if "no puedo" in texto.lower():
        print("¿Has verificado tu conexión a internet?")
    elif "puede" in texto.lower():
        print("¿La persona tiene acceso al email asociado?")

def manejar_contrasena(match_obj):
    print("Problema de contraseña")
    texto = match_obj.group('contrasena')
    if "olvid" in texto.lower():
        print("Puedes resetear tu contraseña aquí: [link]")
    elif "cambiar" in texto.lower():
        print("Para cambiar contraseña: Tu Cuenta > Seguridad")

def manejar_bloqueo(match_obj):
    print("Problema de cuenta bloqueada")
    print("Sigue estos pasos para desbloquear tu cuenta: [link]")

#Manejadores
manejadores_gestion = {
    'acceso': manejar_acceso,
    'contrasena': manejar_contrasena,
    'bloqueo': manejar_bloqueo,
    # 'verificacion': manejar_verificacion
}

# Respuestas específicas por categoría
respuestas = {
    Categoria.GESTION_CUENTA: [
        "Para problemas de acceso, intenta restablecer tu contraseña aquí: [link]",
        "Si tu cuenta está bloqueada, sigue estos pasos: [link]",
        "Para cambiar tu correo o teléfono, ve a Tu Cuenta > Configuración",
        "Si necesitas ayuda con la verificación en dos pasos, consulta: [link]"
    ],
    Categoria.PRIME_SUSCRIPCIONES: [

    ],
    Categoria.SOPORTE_TECNICO: [
        
    ]
}

state = 0
salida = True
categoria_actual = None
match_objeto = None

# Flujo de conversación
print("Bot: ¡Hola! Soy tu asistente virtual de Amazon. ¿En qué te puedo ayudar hoy?")

while salida:
    try:
        if state == 0:
            # time.sleep(1)
            user_input = input("Bot: Por favor, describe tu situación:\nUsuario: ")

            categoria_actual, match_objeto = clasificar_consulta(user_input)

            if categoria_actual != Categoria.NO_RECONOCIDO:
                print("Grupos capturados:", match_objeto.groupdict())
                print(f"Bot: Entiendo, tienes una consulta sobre {categoria_actual.name.replace('_', ' ').title()}.")
                if categoria_actual == Categoria.GESTION_CUENTA and match_objeto:
                    grupos = match_objeto.groupdict()
                    print("Bot: Analizando tu consulta...")
                    
                    # Ejecutar manejadores específicos para cada grupo que coincidió
                    for grupo_nombre, grupo_valor in grupos.items():
                        if grupo_valor and grupo_nombre in manejadores_gestion:
                            manejadores_gestion[grupo_nombre](match_objeto)
                state = 1                
            else:
                print("Bot: Lo siento, no he entendido tu consulta. ¿Podrías reformularla?")
                
        elif state == 1:
            time.sleep(1)
            print("Bot: ¿Puedo ayudarte con algo más?")
            user_input = input("Usuario: ").strip().lower()
            if no_RE.match(user_input):
                despedida = random.choice(despedidas)
                print(f"Bot: {despedida}")
                salida = False
            elif si_RE.match(user_input):
                state = 0
                print("Bot: Perfecto, ¿en qué más puedo ayudarte?")
            else:
                print("Bot: No he entendido tu respuesta.")
                continue

    except KeyboardInterrupt:
        print("\nGracias por usar el chatbot de Amazon. ¡Hasta pronto!")
        break