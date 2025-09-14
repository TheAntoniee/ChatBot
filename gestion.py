import re
import time
import random
from enum import Enum

class Categoria(Enum):
    GESTION_CUENTA = 1
    PRIME_SUSCRIPCIONES = 2
    SOPORTE_TECNICO = 3
    NO_RECONOCIDO = 4


# ---------------------------
# Expresiones de cortesía y empatía
# ---------------------------
saludos = [
    "Bot: ¡Hola! Soy tu asistente virtual de Amazon. Me da mucho gusto ayudarte hoy.",
    "Bot: ¡Hola! Bienvenido al soporte de Amazon. Estoy aquí para asistirte.",
    "Bot: ¡Hola! Gracias por contactar al soporte de Amazon. ¿En qué puedo ayudarte?"
]
expresiones_empatia = [
    "Bot: Entiendo lo frustrante que puede ser cuando {problema}.",
    "Bot: Comprendo tu preocupación sobre {problema}, déjame ayudarte.",
    "Bot: Lamento escuchar que estás teniendo dificultades con {problema}.",
    "Bot: Sé lo importante que es resolver {problema}, trabajemos juntos en esto.",
    "Bot: Lamentamos que tengas problemas para {problema}, estamos aquí para ayudarte."
]
confirmaciones = [
    "Bot: Perfecto, he entendido que necesitas ayuda con {tema}.",
    "Bot: De acuerdo, veo que tu consulta es sobre {tema}.",
    "Bot: Entendido, me enfocaré en ayudarte con {tema}."
]
despedidas = [
    "Bot: ¡Ha sido un placer ayudarte! Que tengas un excelente día.",
    "Bot: Gracias por confiar en Amazon. ¡Hasta pronto!",
    "Bot: Espero haberte sido de ayuda. ¡Cuídate mucho!",
    "Bot: No dudes en contactarnos si necesitas más ayuda. ¡Adiós!"
]

# ---------------------------
# Expresiones regulares
# ---------------------------
email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
telefono_regex = r'^\+?[0-9]{7,15}$'
nombre_regex = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$'
tarjeta_regex = r'^\d{16}$'
direccion_regex = r'^[\w\s\#\-\.,áéíóúÁÉÍÓÚñÑ]+$'

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
        |(?P<bloqueo>(?:bloque[o]|bloqueada|suspendida)\s+cuenta|cuenta\s+(?:bloque[ao]|bloqueada|suspendida))
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

# ---------------------------
# Clasificación de consulta
# ---------------------------
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

# ---------------------------
# Función para manejar preguntas
# ---------------------------
def hacer_pregunta(pregunta, intentos=3):
    for intento in range(intentos):
        print(f"Bot: {pregunta}")
        respuesta = input("Usuario: ").strip().lower()
        if si_RE.match(respuesta) or no_RE.match(respuesta):
            return respuesta
        if intento < intentos - 1:
            print("Bot: No entendí tu respuesta. ¿Podrías responder nuevamente'?")
        else:
            print("Bot: Continuemos, asumiré que necesitas ayuda...")
            return "no"  # Por defecto para continuar el flujo
    return "no"

# ---------------------------
# Respuestas
# ---------------------------
def manejar_acceso(match_obj):
    print("Bot: A veces, para mayor seguridad, enviamos un correo electrónico de verificación de cuenta.")
    respuesta = hacer_pregunta("¿Has revisado tu correo electrónico para un enlace o código de verificación?")
    if no_RE.match(respuesta):
        hacer_pregunta("Por favor revisa tu correo, incluyendo la carpeta de spam. ¿Encontraste el correo?")
    elif si_RE.match(respuesta):
        hacer_pregunta("¿Pudiste completar la verificación y acceder a tu cuenta?")
        if no_RE.match(respuesta):
            print("Bot: Si el problema persiste, por favor contacta soporte: https://www.amazon.com/gp/help/customer/contact-us")
            state = 0
    return True

def manejar_contrasena(match_obj):
    texto = match_obj.group('contrasena').lower()
    
    if "olvid" not in texto:
        return False
    
    respuesta = hacer_pregunta("¿Ya intentaste visitar nuestra página de 'Restablecimiento de contraseña'?")
    if no_RE.match(respuesta):
        hacer_pregunta("Te recomiendo: https://www.amazon.com/-/es/ap/forgotpassword ¿Necesitas ayuda con los pasos?")
    elif si_RE.match(respuesta):
        respuesta = hacer_pregunta("¿Revisaste tu carpeta de spam/correo no deseado?")
        if no_RE.match(respuesta):
            hacer_pregunta("Por favor revisa spam. ¿Encontraste el correo?")
        elif si_RE.match(respuesta):
            hacer_pregunta("¿Tienes acceso al email asociado o necesitas ayuda para recuperarlo?")
            if no_RE.match(respuesta):
                print("Bot: Por favor contacta soporte: https://www.amazon.com/gp/help/customer/contact-us")
                state = 0
    return True

def manejar_bloqueo(match_obj):
    respuesta = hacer_pregunta("¿Recibiste alguna notificación o correo explicando el motivo del bloqueo?")
    if si_RE.match(respuesta):
        hacer_pregunta("¿Pudiste seguir las instrucciones para desbloquear tu cuenta?")
        if no_RE.match(respuesta):
            print("Bot: Por favor contacta soporte: https://www.amazon.com/gp/help/customer/contact-us")
            state = 0
    elif no_RE.match(respuesta):
        hacer_pregunta("Te recomiendo visitar: https://www.amazon.com/gp/help/customer/contact-us ¿Necesitas ayuda con los pasos?")
    return True

# ---------------------------
# Maneajadores de gestión de cuenta
# ---------------------------
manejadores_gestion = {
    'acceso': manejar_acceso,
    'contrasena': manejar_contrasena,
    'bloqueo': manejar_bloqueo,
    # 'verificacion': manejar_verificacion
}

state = 0
salida = True
categoria_actual = None
match_objeto = None

# ---------------------------
# Flujo chatbot
# ---------------------------
print("Bot: ¡Hola! Soy tu asistente virtual de Amazon. ¿En qué te puedo ayudar hoy?")

while salida:
    try:
        if state == 0:
            # time.sleep(1)
            user_input = input("Bot: Por favor, describe tu situación:\nUsuario: ")

            categoria_actual, match_objeto = clasificar_consulta(user_input)
            if categoria_actual != Categoria.NO_RECONOCIDO:
                print(expresiones_empatia[0].format(problema=user_input))

                if categoria_actual == Categoria.GESTION_CUENTA and match_objeto:
                    grupos = match_objeto.groupdict()
                    
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