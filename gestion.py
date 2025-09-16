import re
import time
import random
import csv
import os
import unicodedata
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

cambiar_contrasena = re.compile(r"""
    (?ix)
    \b(?:
        ((?:olvid[ée]|perd[ií]|recuperar|restablecer|resetear|cambiar)\s+(?:mi|la\s+)?(?:contraseñ[ao]|password|clave|pass|pwd))
        (?:mi\s+)?(?:contraseñ[ao]|password|clave|pass|pwd)
    )\b
""", re.VERBOSE)
ingresar_cuenta_RE = re.compile(r"""
    (?ix)
    \b(?:
        # Problemas de acceso
        (?:no\s+me\s+deja|no\s+funciona|no\s+reconoce|me\s+da\s+error|tengo\s+problemas\s+para|no\s+puedo|podr[ií]a)\s*?
        (?:ingresar|entrar|acceder|login|log\s+in|sign\s+in|iniciar\s+sesi[oó]n|abrir\s+sesi[oó]n|loguear|loguearme)?
        (?:\s+(?:a|en|mi|la|tu|su|nuestro|nuestra|sus))*?
        (?:\s+(?:cuenta|account|perfil|profile|sistema|plataforma))?
        (?:\s+(?:de|del|la|el|los|las))*?
        (?:\s+(?:amazon|sitio|web|p[aá]gina|app|aplicaci[oó]n|plataforma))?
        |(?:error|problema|fallo|incidente)\s+(?:al|al\s+intentar|al\s+tratar\s+de)\s+
        |(?:usuario|correo|email|contraseña|password)\s+(?:no\s+funciona|no\s+sirve|incorrecto|no\s+reconoce)
        |(?:nunca\s+puedo|no\s+puedo\s+iniciar\s+sesi[oó]n|siempre\s+me\s+pasa|vuelve\s+a\s+fallar)\s+
    )\b
""", re.VERBOSE)
actualizar_datos_RE = re.compile(r"""
    (?ix)
    \b(?:
        |(?:quiero|me\s+gustar[ií]a|necesito|debo|tengo\s+que|deseo|es\s+necesario|es\s+importante)
        (?:actualizar|cambiar|modificar|editar|restablecer|restaurar|revisar|verificar)
        (?:\s+(?:mi|la|tu|su|nuestro|nuestra|sus))*
        \s+(?:informaci[óo]n|datos|data|details|detalles)
        (?:\s+(?:de|del|la|el|los|las))*
        \s+(?:cuenta|account|perfil|profile)
        (de|del|la|el|los|las|amazon|sistema|sitio|web|pagina|app|aplicacion)*?
    )\b
""", re.VERBOSE)

crear_cuenta_RE = re.compile(r"""
    (?ix)
    \b(?:
        (?:quiero|me\s+gustar[ií]a|necesito|debo|tengo\s+que|deseo|es\s+necesario|es\s+importante)?
        (?:crear|hacer|abrir|iniciar|registr(?:arme|arse)|nueva\s+)
        (?:\s+(?:una|la))*
        \s+(?:cuenta|account|perfil|profile)
    )\b
""", re.VERBOSE)

problemas_verificacion_RE = re.compile(r"""
    (?ix)
    \b(?:
        (?:tengo|hay|existe|me\s+da|me\s+aparece|no\s+puedo|no\s+recibo|no\s+llega|no\s+me\s+llega|no\s+me\s+han\s+enviado)?
        (?:problema[s]|error[es]|dificultad[es]|duda[s])
        (?:\s+(?:con|de|para))*
        \s+(?:autenticaci[óo]n|verificaci[óo]n|2fa|doble\s+factor|c[óo]digo)
    )\b
""", re.VERBOSE)

bloqueo_cuenta_RE = re.compile(r"""
    (?ix)
    \b(?:
        (?:me|mi|la)?\s*cuenta
        (?:\s+(?:de|del|la|el|los|las|amazon|sistema|sitio|web|pagina|app|aplicacion|mi|tu|su|nuestro|nuestra|sus))*
        \s+(?:tengo|est[aá]|se\s+encuentra|qued[óo]|fue|aparece)
        \s+(?:bloquead[ao]s?|suspendid[ao]s?|inhabilitad[ao]s?)
        |aparece\s+(?:bloquead[ao]s?|suspendid[ao]s?|inhabilitad[ao]s?)\s+(?:mi|la)?\s*cuenta
        |((esta\s+bloqueada|bloqueada|suspendida|inhabilitada)\s+(?:mi|la)?\s*cuenta)
        |tengo\s+(?:mi|la)?\s*cuenta\s+(?:bloquead[ao]s?|suspendid[ao]s?|inhabilitad[ao]s?)
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
no_RE = re.compile(r'^(?:no|nada|cancelar|negativo|nel|nah||n|no,?\s+gracias)$', re.IGNORECASE)
si_RE = re.compile(r'^(?:s[ií]|s|ok|perfecto|positivo|correcto|acepto|claro|por\s+supuesto|afirmativo|simon|smn)$', re.IGNORECASE)

# ---------------------------
# Clasificación de consulta
# ---------------------------
def normalizar(texto):
    # Pasamos a minúsculas y eliminamos tildes
    texto = texto.lower()
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

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
        if si_RE.match(respuesta):
            return "si"
        elif no_RE.match(respuesta):
            return "no"
        if intento < intentos - 1:
            print("Bot: No entendí tu respuesta. ¿Podrías responder nuevamente'?")
        else:
            print("Bot: Continuemos, asumiré que necesitas ayuda...")
            return "no"
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
    print(texto)
    if "olvid" not in texto and "perd" not in texto:
        return False
    respuesta = hacer_pregunta("¿Ya intentaste visitar nuestra página de 'Restablecimiento de contraseña'?")
    if no_RE.match(respuesta):
        respuesta = hacer_pregunta("Te recomiendo: https://www.amazon.com/-/es/ap/forgotpassword ¿Necesitas ayuda con los pasos?")
        if si_RE.match(respuesta):
            print("Bot: Por favor visita el enlace y sigue las instrucciones.")
        else:
            print("Bot: Entiendo. El enlace estará disponible si lo necesitas.")
    elif si_RE.match(respuesta):
        respuesta = hacer_pregunta("¿Revisaste tu carpeta de spam/correo no deseado?")
        if no_RE.match(respuesta):
            respuesta = hacer_pregunta("Por favor revisa spam. ¿Encontraste el correo?")
        elif si_RE.match(respuesta):
            respuesta = hacer_pregunta("¿Tienes acceso al email asociado o necesitas ayuda para recuperarlo?")
            if no_RE.match(respuesta):
                print("Bot: Por favor contacta soporte: https://www.amazon.com/gp/help/customer/contact-us")
            # else 
    return True

def manejar_bloqueo(match_obj):
    respuesta = hacer_pregunta("Bot: ¿Recibiste alguna notificación o correo explicando el motivo del bloqueo?")
    if si_RE.match(respuesta):
        print("Bot: Por favor sigue las instrucciones en el correo para desbloquear tu cuenta.")
    elif no_RE.match(respuesta):
        print("Bot: Para restaurar el acceso, inicia sesión en tu cuenta de Amazon y completa el formulario que incluye los archivos adjuntos necesarios.")
        respuesta = hacer_pregunta("Bot: ¿Ya enviaste el formulario?")
        if si_RE.match(respuesta):
            print("Bot: Espera 24 horas para recibir más actualizaciones de nuestra parte.")
        elif no_RE.match(respuesta):
            print("Bot: Por favor envía el formulario para iniciar el proceso de desbloqueo.")
    return True

def manejar_verificacion(match_obj):
    respuesta = hacer_pregunta("¿Recibiste el código en tu dispositivo o correo?")
    if respuesta == "no":
        print("Bot: Revisa tu carpeta de spam o actualiza tu número en configuración de seguridad.")
    print("Bot: También puedes administrar la verificación aquí: https://www.amazon.com/a/settings/approval")
    return True

def manejar_datos(match_obj):
    print("Bot: Para actualizar correo, teléfono o dirección:")
    print("Bot: Ingresa a: https://www.amazon.com/a/central y selecciona 'Información de inicio de sesión y seguridad'.")
    return True

def manejar_crearCuenta(match_obj):
    respuesta = hacer_pregunta(print("Bot: ¿Necesitas ayuda para crear una cuenta nueva en Amazon?"))
    if si_RE.match(respuesta):
        respuesta = hacer_pregunta("¿Te gustaría que te guíe en el proceso de creación de cuenta?")
        if si_RE.match(respuesta):
            # Pregunta de seguimiento para entender mejor la necesidad
            print("Bot: Perfecto. ¿Estás teniendo algún problema en particular o solo necesitas el enlace?")
            user_input = input("Usuario: ").strip().lower()
            
            if any(palabra in user_input for palabra in ["problema", "error", "dificultad", "no puedo"]):
                print("Bot: Entiendo. ¿Podrías describirme qué error o mensaje te aparece?")
                problema = input("Usuario: ").strip().lower()
                # Manejar problemas específicos
                if "correo" in problema or "email" in problema:
                    print("Bot: Si el correo ya está registrado:")
                    print("- Prueba con otra dirección de email")
                    print("- O recupera la cuenta existente: https://www.amazon.com/-/es/ap/forgotpassword")
                elif "contraseña" in problema:
                    print("Bot: La contraseña debe tener al menos 8 caracteres, con letras mayúsculas, minúsculas y números.")
                else:
                    print("Bot: Te recomiendo:")
                    print("1. Verificar tu conexión a internet")
                    print("2. Usar un navegador actualizado")
                    print("3. Aquí tienes el enlace: https://www.amazon.com/ap/register")
            else:
                # Solo el enlace
                print("Bot: Aquí tienes el enlace para crear tu cuenta: https://www.amazon.com/ap/register")
                print("Bot: El proceso es sencillo: email, contraseña y datos básicos. ¡Suerte!")
                
        else:
            # Usuario no quiere ayuda
            print("Bot: De acuerdo. Si cambias de opinión o necesitas ayuda más adelante, estaré aquí.")
            print("Bot: También puedes visitar: https://www.amazon.com/ap/register cuando lo necesites.")
    return True

# ---------------------------
# Maneajadores de gestión de cuenta
# ---------------------------
manejadores_gestion = {
    'acceso': manejar_acceso,
    'contrasena': manejar_contrasena,
    'bloqueo': manejar_bloqueo,
    'verificacion': manejar_verificacion,
    'datos': manejar_datos,
    'crearCuenta': manejar_crearCuenta
}

state = 0
salida = True
categoria_actual = None

# ---------------------------
# Flujo chatbot
# ---------------------------
print("Bot: ¡Hola! Soy tu asistente virtual de Amazon. ¿En qué te puedo ayudar hoy?")

while salida:
    try:
        if state == 0:
            user_input = input("Bot: Por favor, describe tu situación:\nUsuario: ")
            empatia = random.choice(expresiones_empatia)
            print(empatia.format(problema=user_input))

            if ingresar_cuenta_RE.findall(user_input) != []:
                manejar_acceso("acceso")
                state = 1
            if cambiar_contrasena.findall(user_input) != []:
                manejar_contrasena("contrasena")
                state = 2
            if actualizar_datos_RE.findall(user_input) != []:
                manejar_datos("datos")  
                state = 3
            if bloqueo_cuenta_RE.findall(user_input) != []:
                manejar_bloqueo("bloqueo") 
                state = 4
            if crear_cuenta_RE.findall(user_input) != []:
                manejar_crearCuenta("crearCuenta")
                state = 5
            if problemas_verificacion_RE.findall(user_input) != []:
                manejar_verificacion("verificacion")
                state = 6
            if actualizar_datos_RE.findall(user_input) != []:
                state = 7
            else: 
                print("Bot: Lo siento, no he entendido tu consulta. ¿Podrías reformularla?")
                
        elif state == 99:
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