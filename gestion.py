# Gestión de cuenta y seguridad
# Amazon Prime y suscripciones
# Soporte técnico de dispositivos

import re

#Expresiones regulares generales
email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
telefono_regex = r'^\+?[0-9]{7,15}$'
nombre_regex = r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$'

# Expresiones regulares de cuenta y seguridad
Cuenta_Regex = r"(?i)\b(cuenta|(iniciar|cerrar) sesi[oó]n|(recuperar )?contraseña|verificaci[oó]n|en dos pasos|seguridad|privacidad|datos personales|configuraci[oó]n|notificaciones|autenticaci[oó]n|biometr[íi]a|huella digital|reconocimiento facial|PIN|seguro|protecci[oó]n|alertas|historial de actividad|dispositivos conectados|cerrar todas las sesiones|cambiar (correo electr[oó]nico|n[úu]mero de tel[ée]fono)|eliminar cuenta)\b"

while True:
    try:
        user_input = input("Ingrese un término relacionado con la gestión de cuenta y seguridad: ")
        if user_input.lower() == 'salir':
            break
        if re.search(Cuenta_Regex, user_input):
            print(f"'{user_input}' válido")
        else:
            print(f"'{user_input}' no válido")
    except Exception as e:
        print(f"Error: {e}")
        break