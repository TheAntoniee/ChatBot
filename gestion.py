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
    DISPOSITIVOS = 4
    BLOQUEO_CUENTA = 5
    CONTRASENA = 6
    CREAR_CUENTA = 7
    VERIFICACION = 8
    NO_RECONOCIDO = 99


# ---------------------------
# Expresiones de cortesía y empatía
# ---------------------------
saludos = [
    "¡Hola! Soy tu asistente virtual de Amazon. Me da mucho gusto ayudarte hoy.",
    "¡Hola! Bienvenido al soporte de Amazon. Estoy aquí para asistirte.",
    "¡Hola! Gracias por contactar al soporte de Amazon. ¿En qué puedo ayudarte?"
]
expresiones_empatia = [
    "Entiendo lo frustrante que puede ser cuando {problema}.",
    "Comprendo tu preocupación sobre {problema}, déjame ayudarte.",
    "Lamento escuchar que estás teniendo dificultades con {problema}.",
    "Sé lo importante que es resolver {problema}, trabajemos juntos en esto.",
    "Lamentamos que tengas problemas para {problema}, estamos aquí para ayudarte."
]
confirmaciones = [
    "Perfecto, he entendido que necesitas ayuda con {tema}.",
    "De acuerdo, veo que tu consulta es sobre {tema}.",
    "Entendido, me enfocaré en ayudarte con {tema}."
]
despedidas = [
    "¡Ha sido un placer ayudarte! Que tengas un excelente día.",
    "Gracias por confiar en Amazon. ¡Hasta pronto!",
    "Espero haberte sido de ayuda. ¡Cuídate mucho!",
    "No dudes en contactarnos si necesitas más ayuda. ¡Adiós!"
]

# ---------------------------
# Expresiones regulares
# ---------------------------
email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
telefono_regex = r'^\+?[0-9]{7,15}$'
nombre_regex = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$'
tarjeta_regex = r'^\d{16}$'
direccion_regex = r'^[\w\s\#\-\.,áéíóúÁÉÍÓÚñÑ]+$'

cambiar_contrasena_RE = re.compile(r"""
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
        (?:actualizar|cambiar|modificar|editar|restablecer|restaurar|revisar|verificar)
        (?:\s+(?:mi|la|tu|su|nuestro|nuestra|sus))*
        \s+(?:informaci[óo]n|datos|data|details|detalles)
        (?:\s+(?:de|del|la|el|los|las))*
        \s+(?:cuenta|account|perfil|profile)
        (de|del|la|el|los|las|amazon|sistema|sitio|web|pagina|app|aplicacion)*?
        |(?:quiero|me\s+gustar[ií]a|necesito|debo|tengo\s+que|deseo|es\s+necesario|es\s+importante)
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
        (?P<suscripcion>
            (?:\s+(?:mi|la|tu|su|el|))*?
            (?:quiero|necesito|deseo|me\s+gustar[ií]a|tengo\s+que|debo|es\s+importante|es\s+necesario)?\s*
            (?:de|l|la|los|las|mi|tu|su|nuestro|nuestra|sus)?\s*
            (?:prime|suscripción|membresía|anual|mensual|gratis|prueba|renovación|cancelar|reactivar|beneficios|envío gratis
            |prime video|prime music|prime gaming|prime reading|kindle unlimited|amazon music|amazon video|amazon photos|almacenamiento ilimitado
            |oferta|descuento|promoción|factura|recibo|pago|método de pago|día prime|prime day|devolución|reembolso|garantía))
    )\b
""", re.VERBOSE)
Soporte_Tecnico_RE = re.compile(r"""
    (?ix)
    \b(?:
        # Soporte técnico
        (?P<soporte>(?:dispositivo|kindle|fire tv|echo|alexa|fire tablet|fire stick|ring|blink|setup|configurar|conectar|wifi|bluetooth|actualización|firmware|software|hardware|pantalla|batería|carga|encender|apagar|reiniciar|resetear|restablecer fábrica|problema|error|fallo|no funciona|lento|congelado|térmico|sobrecalentamiento|garantía|reparación|reemplazo|troubleshooting|solución|guía|manual|instrucciones|compatibilidad|drivers|controladores))
    )\b
""", re.VERBOSE)
no_RE = re.compile(r'^(?:no|nada|cancelar|negativo|nel|nah|n|no?\s+gracias)$', re.IGNORECASE)
si_RE = re.compile(r'^(?:s[ií]|s|ok|perfecto|positivo|entendido|correcto|acepto|claro|por\s+supuesto|afirmativo|simon|smn)$', re.IGNORECASE)

Dispositivos_RE = re.compile(r"""
    (?ix)
    \b(?:
        (?:registrar|conectar|actualizar|configura(?:r|ción|do)|empareja(?:r|do)|sincroniza(?:r|do))?\s*
        (?:el|la|mi|su|tu|nuestro|dispositivo)?\s*
        echo|alexa|kindle|fire\s*tv|fire\s*stick|fire\s*tablet|ring|blink|dot|show|spot|cube|paperwhite
    )\b
""", re.VERBOSE)

# ---------------------------
# Mapa de categorías
# ---------------------------
patrones = {
    Categoria.GESTION_CUENTA: ingresar_cuenta_RE,
    Categoria.CONTRASENA: cambiar_contrasena_RE,
    Categoria.BLOQUEO_CUENTA: bloqueo_cuenta_RE,
    Categoria.CREAR_CUENTA: crear_cuenta_RE,
    Categoria.VERIFICACION: problemas_verificacion_RE,
    Categoria.PRIME_SUSCRIPCIONES: Prime_Suscripciones_RE,
    Categoria.DISPOSITIVOS: Dispositivos_RE
}
# ---------------------------
# Diccinonario de dispositivos y problemas
# ---------------------------
dispositivos = {
    "echo": {
        "no responde": "Reinicia el dispositivo y verifica Wi-Fi y micrófono.",
        "problema con wi-fi": "Reinicia router y Echo, o reconfigura en la app Alexa.",
        "configurar": "Abre la app Alexa, selecciona 'Dispositivos' → '+' → 'Agregar dispositivo' y sigue los pasos."
    },
    "kindle": {
        "no carga": "Usa cargador original y reinicia manteniendo el botón 40s.",
        "pantalla congelada": "Reinicia o espera que cargue completamente."
    },
    "fire tv": {
        "no enciende": "Verifica HDMI y alimentación.",
        "mando no funciona": "Revisa baterías y vuelve a vincular el mando."
    },
    "fire tablet": {
        "se congela": "Reinicia el dispositivo o borra caché."
    }
}
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

# Clasificador
def clasificar_consulta(texto: str) -> Categoria:
    for categoria, regex in patrones.items():
        if regex.search(texto):
            return categoria
    return Categoria.NO_RECONOCIDO

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
            writer.writerow(["taniagsr3@gmail.com", "activo"])

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

def reactivar_suscripcion(email):
    filas = []
    encontrado = False
    with open("suscripciones.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["email"].lower() == email.lower():
                if row["estado"] == "cancelado":
                    row["estado"] = "activo"
                    encontrado = True
            filas.append(row)
    if encontrado:
        with open("suscripciones.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["email", "estado"])
            writer.writeheader()
            writer.writerows(filas)
    return encontrado

def iniciar_prueba(email):
    filas = []
    iniciado = False
    with open("suscripciones.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["email"].lower() == email.lower():
                if row["estado"] == "cancelado":
                    row["estado"] = "activo (prueba gratuita)"
                    iniciado = True
            filas.append(row)
    if iniciado:
        with open("suscripciones.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["email", "estado"])
            writer.writeheader()
            writer.writerows(filas)
    return iniciado

def mostrar_beneficios():
    beneficios = [
        "✅ Envíos gratis en productos Prime",
        "✅ Prime Video incluido",
        "✅ Prime Music",
        "✅ Prime Reading (libros y revistas)",
        "✅ Ofertas exclusivas en Prime Day"
    ]
    print("\nTu suscripción Prime incluye:")
    for b in beneficios:
        print("-", b)

# ---------------------------
# Función para manejar preguntas
# ---------------------------
def hacer_pregunta(pregunta, intentos=3):
    for intento in range(intentos):
        print(f" {pregunta}")
        respuesta = input("").strip().lower()
        if si_RE.match(respuesta):
            return "si"
        elif no_RE.match(respuesta):
            return "no"
        if intento < intentos - 1:
            print(" No entendí tu respuesta. ¿Podrías responder nuevamente'?")
        else:
            print(" Continuemos, asumiré que necesitas ayuda...")
            return "no"
    return "no"

# ---------------------------
# Respuestas
# ---------------------------
def manejar_acceso(match_obj):
    print(" A veces, para mayor seguridad, enviamos un correo electrónico de verificación de cuenta.")
    respuesta = hacer_pregunta("¿Has revisado tu correo electrónico para un enlace o código de verificación?")
    if no_RE.match(respuesta):
        hacer_pregunta("Por favor revisa tu correo, incluyendo la carpeta de spam. ¿Encontraste el correo?")
    elif si_RE.match(respuesta):
        hacer_pregunta("¿Pudiste completar la verificación y acceder a tu cuenta?")
        if no_RE.match(respuesta):
            print(" Si el problema persiste, por favor contacta soporte: https://www.amazon.com/gp/help/customer/contact-us")
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
            print(" Por favor visita el enlace y sigue las instrucciones.")
        else:
            print(" Entiendo. El enlace estará disponible si lo necesitas.")
    elif si_RE.match(respuesta):
        respuesta = hacer_pregunta("¿Revisaste tu carpeta de spam/correo no deseado?")
        if no_RE.match(respuesta):
            respuesta = hacer_pregunta("Por favor revisa spam. ¿Encontraste el correo?")
        elif si_RE.match(respuesta):
            respuesta = hacer_pregunta("¿Tienes acceso al email asociado o necesitas ayuda para recuperarlo?")
            if no_RE.match(respuesta):
                print(" Por favor contacta soporte: https://www.amazon.com/gp/help/customer/contact-us")
            # else 
    return True

def manejar_bloqueo(match_obj):
    respuesta = hacer_pregunta(" ¿Recibiste alguna notificación o correo explicando el motivo del bloqueo?")
    if si_RE.match(respuesta):
        print(" Por favor sigue las instrucciones en el correo para desbloquear tu cuenta.")
    elif no_RE.match(respuesta):
        print(" Para restaurar el acceso, inicia sesión en tu cuenta de Amazon y completa el formulario que incluye los archivos adjuntos necesarios.")
        respuesta = hacer_pregunta(" ¿Ya enviaste el formulario?")
        if si_RE.match(respuesta):
            print(" Espera 24 horas para recibir más actualizaciones de nuestra parte.")
        elif no_RE.match(respuesta):
            print(" Por favor envía el formulario para iniciar el proceso de desbloqueo.")
    return True

def manejar_verificacion(match_obj):
    respuesta = hacer_pregunta("¿Recibiste el código en tu dispositivo o correo?")
    if respuesta == "no":
        print(" Revisa tu carpeta de spam o actualiza tu número en configuración de seguridad.")
    print(" También puedes administrar la verificación aquí: https://www.amazon.com/a/settings/approval")
    return True

def manejar_datos(match_obj):
    print(" Para actualizar correo, teléfono o dirección:")
    print(" Ingresa a: https://www.amazon.com/a/central y selecciona 'Información de inicio de sesión y seguridad'.")
    return True

def manejar_crearCuenta(match_obj):
    respuesta = hacer_pregunta(print(" ¿Necesitas ayuda para crear una cuenta nueva en Amazon?"))
    if si_RE.match(respuesta):
        respuesta = hacer_pregunta("¿Te gustaría que te guíe en el proceso de creación de cuenta?")
        if si_RE.match(respuesta):
            # Pregunta de seguimiento para entender mejor la necesidad
            print(" Perfecto. ¿Estás teniendo algún problema en particular o solo necesitas el enlace?")
            user_input = input("").strip().lower()
            
            if any(palabra in user_input for palabra in ["problema", "error", "dificultad", "no puedo"]):
                print(" Entiendo. ¿Podrías describirme qué error o mensaje te aparece?")
                problema = input("").strip().lower()
                # Manejar problemas específicos
                if "correo" in problema or "email" in problema:
                    print(" Si el correo ya está registrado:")
                    print("- Prueba con otra dirección de email")
                    print("- O recupera la cuenta existente: https://www.amazon.com/-/es/ap/forgotpassword")
                elif "contraseña" in problema:
                    print(" La contraseña debe tener al menos 8 caracteres, con letras mayúsculas, minúsculas y números.")
                else:
                    print(" Te recomiendo:")
                    print("1. Verificar tu conexión a internet")
                    print("2. Usar un navegador actualizado")
                    print("3. Aquí tienes el enlace: https://www.amazon.com/ap/register")
            else:
                # Solo el enlace
                print(" Aquí tienes el enlace para crear tu cuenta: https://www.amazon.com/ap/register")
                print(" El proceso es sencillo: email, contraseña y datos básicos. ¡Suerte!")
                
        else:
            # Usuario no quiere ayuda
            print(" De acuerdo. Si cambias de opinión o necesitas ayuda más adelante, estaré aquí.")
            print(" También puedes visitar: https://www.amazon.com/ap/register cuando lo necesites.")
    return True

def manejar_configuraciónDispositivo(match_obj):
    print("\nRegistrar un e-reader Kindle totalmente nuevo: Cuando enciendas el Kindle, sigue las instrucciones que aparecen en pantalla para conectarte a una red wifi y configurar el dispositivo.")
    respuesta = hacer_pregunta("¿Tienes problemas para registrarte?")
    if si_RE.match(respuesta):
        respuesta = hacer_pregunta("¿Tienes problemas con la contraseña?")
        if si_RE.match(respuesta):
            print("Si recibes un error de contraseña o has olvidado la contraseña de tu cuenta Amazon, puedes restablecerla aquí: https://www.amazon.com/ap/forgotpassword")
        elif no_RE.match(respuesta):
            respuesta = hacer_pregunta("¿Tienes problemas con el inicio de sesión en la cuenta de amazon?")
            if si_RE.match(respuesta):
                print("Comprueba si te has registrado en la cuenta Amazon correcta. Si tienes varias cuentas, valida las credenciales de inicio de sesión en otro dispositivo.")
            elif no_RE.match(respuesta):
                respuesta = hacer_pregunta("¿Tienes problemas de conectividad inalámbrica?")
                if si_RE.match(respuesta):
                    print("Si tienes problemas para conectar el dispositivo a una red inalámbrica, sigue los pasos de resolución de problemas que se describen en esta página de ayuda:Solucionar problemas con la conexión wifi en el e-reader Kindle.")
                elif no_RE.match(respuesta):
                    print("Si tienes problemas para registrar el dispositivo, ponte en contacto con el servicio de atención al cliente de Amazon.")
    elif no_RE.match(respuesta):
        respuesta = hacer_pregunta("¿El dispositivo es regalado?")
        if si_RE.match(respuesta):
            print("Al restablecer la configuración predeterminada, el dispositivo volverá a la configuración original, y se eliminarán así todos tus datos personales, el contenido descargado y el contenido que no se haya sincronizado.")
            print("1. En la pantalla de inicio, desliza el dedo hacia abajo para abrir el menú Acciones rápidas o selecciona Menú.")
            print("2. Selecciona Configuración o Toda la configuración.")
            print("3. Ve a Opciones de dispositivo o selecciona Menú.")
            print("4. Selecciona Restablecer configuración predeterminada. En dispositivos antiguos, selecciona Restablecer dispositivo de nuevo.")
            print("5. Cuando se te pida, selecciona Sí para confirmar.")
    else: 
        state = 0 
    return True

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
inicializar_csv()

saludo  = random.choice(saludos)
print(saludo)

while salida:
    try:
        if state == 0:
            user_input = input("Por favor, describe tu situación:\n").strip().lower()
            if si_RE.match(user_input) or no_RE.match(user_input):
                print("Por favor, describe tu situación con más detalle.")
                continue
                
            categoria_actual = clasificar_consulta(user_input)
            empatia = random.choice(expresiones_empatia)
            print(empatia.format(problema=user_input))

            #---------------------------
            #GESTIONAR CUENTA DE USUARIO
            #---------------------------
            if categoria_actual == Categoria.GESTION_CUENTA:
                manejar_acceso("acceso")
                # state = 1
            elif categoria_actual == Categoria.CONTRASENA:
                manejar_contrasena("contrasena")
                # state = 2
            elif categoria_actual == Categoria.BLOQUEO_CUENTA:
                manejar_bloqueo("bloqueo") 
                # state = 4
            elif categoria_actual == Categoria.CREAR_CUENTA:
                manejar_crearCuenta("crearCuenta")
                # state = 5
            elif categoria_actual == Categoria.VERIFICACION:
                manejar_verificacion("verificacion")
                # state = 6
            elif categoria_actual == Categoria.DISPOSITIVOS:
                # Detectar dispositivo mencionado
                dispositivo_encontrado = None
                for disp in dispositivos:
                    if disp in user_input.lower():
                        dispositivo_encontrado = disp
                        break

                if dispositivo_encontrado:
                    print(f"He detectado que tienes problemas con tu {dispositivo_encontrado.capitalize()}.")
                    problema = input("Describe tu problema (ej: 'no responde', 'pantalla congelada'): ").strip().lower()
                    solucion = dispositivos[dispositivo_encontrado].get(problema)
                    if solucion:
                        print(f"Solución sugerida: {solucion}")
                    else:
                        print("Lo siento, no tengo información sobre ese problema específico.")
                else:
                    print("No pude identificar tu dispositivo. Por favor indícalo con más detalle.")

                # state = 7
            elif categoria_actual == Categoria.PRIME_SUSCRIPCIONES:
                email = input("Por favor, dame el correo asociado a tu suscripción Prime: ")
                if re.match(email_regex, email):
                    estado = buscar_suscripcion(email)
                    if estado is None:
                        print("No encontré ninguna suscripción con ese correo.")
                    else:
                        print(f"Estado actual de tu suscripción: {estado}")
                        print("\nOpciones disponibles:")
                        print("1. Cancelar suscripción")
                        print("2. Reactivar suscripción")
                        print("3. Iniciar prueba gratuita")
                        print("4. Ver beneficios")
                        opcion = input("Elige una opción (1-4): ")

                        if opcion == "1":
                            if estado == "cancelado":
                                print("Tu suscripción ya estaba cancelada.")
                            elif cancelar_suscripcion(email):
                                print("Tu suscripción ha sido cancelada exitosamente.")
                            else:
                                print("Ocurrió un error al cancelar la suscripción.")
                        
                        elif opcion == "2":
                            if reactivar_suscripcion(email):
                                print("Tu suscripción ha sido reactivada con éxito.")
                            else:
                                print("No se pudo reactivar. Revisa si estaba cancelada.")
                        
                        elif opcion == "3":
                            if iniciar_prueba(email):
                                print("Prueba gratuita activada. Disfruta de Prime por 30 días.")
                            else:
                                print("No se pudo activar la prueba gratuita (quizá ya tienes una activa).")
                        
                        elif opcion == "4":
                            mostrar_beneficios()
                        
                        else:
                            print("Opción no válida.")
                else:
                    print("El formato del correo no es válido.")
            
            elif actualizar_datos_RE.findall(user_input) != []:
                manejar_datos("datos")  
                # state = 3
            else: 
                print(" Lo siento, no he entendido tu consulta. ¿Podrías reformularla?")
                
            # if categoria_actual in respuestas:
            #     print("\nTe sugiero también:")
            #     for respuesta in respuestas[categoria_actual]:
            #         print(f"- {respuesta}")
            
        elif state == 99:
            time.sleep(1)
            print(" ¿Puedo ayudarte con algo más?")
            user_input = input("").strip().lower()
            if no_RE.match(user_input):
                despedida = random.choice(despedidas)
                print(f" {despedida}")
                salida = False
            elif si_RE.match(user_input):
                state = 0
                print(" Perfecto, ¿en qué más puedo ayudarte?")
            else:
                print(" No he entendido tu respuesta.")
                continue

    except KeyboardInterrupt:
        print("\nGracias por usar el chatbot de Amazon. ¡Hasta pronto!")
        break