# recognizer.py (reemplazo completo)
import re
from typing import Pattern

# =========================
# Frases cortas globales
# =========================

AFIRMAR = r"\b(" + "|".join([
    # Básicas
    r"s[ií]+", r"s[ií],? claro", r"s[ií],? seguro", r"s[ií],? obvio",
    r"claro(?: que s[ií])?", r"claro que (?:yes|yesh)?",
    r"ok(?:ay|ey|i|is|idoki)?", r"oki doki", r"okas?", r"okey va",
    r"de acuerdo", r"conforme", r"correcto", r"exacto", r"cierto", r"afirmativo",
    r"confirmo", r"hecho", r"entendido", r"comprendido", r"vale", r"vale pues",

    # Coloquiales/juveniles/WhatsApp
    r"va(?: que va)?", r"va pues", r"sobres", r"arre", r"[oó]rale", r"c[aá]mara",
    r"de una", r"jalo+", r"me late", r"sim[oó]n", r"eso mero", r"án?dale",
    r"sip+", r"sipo+", r"sipirili", r"seee+", r"seeh+", r"seh"

    # Inglesismos comunes
    r"yes", r"yeah", r"yep", r"yup", r"sure", r"of course", r"definitely", r"obviously",
    r"totally", r"absolutely", r"roger", r"roger that", r"copy that",

    # Expresiones de WhatsApp/memes
    r"s[ií]{2,}u+", r"sip+", r"sipo+", r"sep+", r"seee+", r"seeh+", r"seh",
    r"obvi[oó]", r"obvius", r"obv", r"obvio perro", r"obvio bb",

    # Formales
    r"por supuesto", r"desde luego", r"en efecto", r"tal cual", r"as[ií] es",
    r"as[ií] mismo", r"sin duda", r"indudablemente",

    # Otras creativas
    r"dale", r"dale pues", r"dalee+", r"jalo duro", r"todo bien", r"full sí",
    r"me agrada", r"est[aá] bien", r"bien ah[ií]", r"perfecto", r"listo"
]) + r")\b"


NEGAR = r"\b(" + "|".join([
    r"no+", r"nel(?: pastel)?", r"nelpas", r"nop(?:e)?", r"noup", r"nones",
    r"para nada", r"negativo", r"ni de chiste", r"ni hablar", r"que va",
    r"de ninguna manera", r"de ninguna", r"nunca", r"jam[aá]s", r"olvídalo",
    r"olvidalo", r"na+", r"nanai", r"nah", r"nopas", r"nopis", r"nopity",
    r"nunca jamás", r"ni pensarlo", r"ni a palos", r"ni loco", r"ni de broma",
    r"no way", r"never", r"nope", r"negativo rotundo", r"ni hablar que no",
    r"de ninguna forma", r"en absoluto", r"no lo creo", r"ni madres",
    r"ni madres que sí", r"que no", r"ni de coña", r"ni cagando", r"naaa",
    r"nananana", r"nop nop", r"que vaaa", r"jajaja no", r"no jala",
    r"ni en sueños", r"ni en pedo", r"ni en broma", r"ni loco que sí",
    r"no pues", r"nooo", r"nono", r"nanan", r"negativo total", r"nada que ver",
    r"ni de chingada manera", r"ni madres ni madres", r"nunca de los nuncas",
    r"ni lo sueñes", r"ni loco que no", r"olvídalo pues", r"ni lo pienses",
    r"ni por chinga", r"ni en pedo que sí", r"no hay chance", r"de ninguna manera",
    r"que nooo", r"nada", r"para nada pues", r"ni pensarlo siquiera", r"no puede ser",
    r"ni cagando que sí", r"nopes", r"nopis", r"nada que hacer", r"fuera de discusión",
    r"sin chance", r"no way jose", r"ni de coña que sí", r"nada de eso",
    r"ni de vaina", r"ni en pedo", r"no chingues", r"no manches", r"ni madres que sí",
    r"ni a huevo", r"ni modo", r"nanay", r"nananay", r"nopety", r"negativo friend",
    r"negativo hermano", r"ni lo sueñes", r"nada que hacer", r"ni de pendejo",
    r"ni de pendeja", r"de ninguna madre", r"ni de la chingada", r"ni joda",
    r"no pues nada", r"ni a la de tres", r"ni por tu vida", r"ni por tu madre",
    r"ni en pintura", r"ni en pintura que sí", r"ni loco que lo haga", r"no hay forma",
    r"ni modo que sí", r"jamás de los jamases", r"ni a palo", r"ni de coña",
    r"ni en pedo amigo", r"negativo absoluto", r"no way amigo", r"no way bro",
    r"ni loco que piense", r"ni en tus sueños", r"no chance", r"sin chance amigo",
    r"negativo rotundo",  r"nao nao amigao", r"nada que hacer amigo", r"ni madres amigo"
]) + r")\b"


ATRAS = r"\b(" + "|".join([
    r"atr[aá]s", r"para atr[aá]s", r"pa'? atr[aá]s", r"regres(a|ar)", r"volver",
    r"retroced(e|er)", r"me equivoc[ée]", r"me confund[ií]", r"corregir", r"corrige",
    r"undo", r"deshacer", r"oops", r"err[óo]n", r"reintentar", r"vuelvo",
    r"repito", r"rectificar", r"quiero volver", r"quiero retroceder", r"revertir",
    r"rehacer", r"cambiar", r"modificar", r"volver atr[aá]s", r"pa'? tras", r"back",
    r"retornar", r"retroceso", r"me confund[ií] con", r"corrigiendo", r"vuelvo al paso anterior",
    # Frases largas y naturales
    r"ups,? me equivoqu[eé]", r"perdon,? me equivoqu[eé]", r"no,? mejor regresemos", r"corrige lo que acabo de poner",
    r"quiero deshacer lo que dije", r"dame un paso atr[aá]s", r"volver al inicio",
    r"quiero empezar de nuevo", r"me equivoqu[eé] en eso", r"haz correcci[oó]n",
    r"necesito retroceder", r"volver a la opci[oó]n anterior", r"regresemos un paso",
    r"quitar lo anterior", r"olvida lo que dije", r"me retracto", r"vuelvo a escribir",
    r"quiero corregir eso", r"dame la opci[oó]n previa"
]) + r")\b"


SALIR = r"\b(" + "|".join([
    r"salir", r"terminar", r"cerrar", r"cortar conversaci[oó]n",
    r"cancelar proceso", r"ya no", r"olv[ií]dalo",
    r"chao", r"ad[ií]os", r"bye", r"nos vemos", r"hasta luego",
    r"hasta (?:aqui|aquí|pronto|mañana|la vista)", r"me despido",
    r"eso es todo", r"eso era todo", r"listo gracias",
    r"ok gracias", r"perfecto gracias", r"ya acab[eé]", r"ya est[aá]",
    r"muchas gracias(?:,? (?:eso es todo|me despido|hasta (?:luego|pronto)))?",
    r"mil gracias(?:,? (?:eso es todo|bye|hasta luego))?",
    r"gracias por todo", r"te lo agradezco(?: mucho)?(?:,? (?:eso es todo|me despido))?",
    r"se agradece(?:,? (?:eso es todo|bye))?",
    r"muy amable(?:,? (?:eso es todo|me despido))?",
    r"me voy", r"cierro aqu[ií]", r"con eso basta"
]) + r")\b"


AYUDA   = r"\b(" + "|".join([
    r"ayuda", r"ay[uú]dame", r"no entiendo", r"que puedo hacer", r"qu[eé] puedo hacer",
    r"como funciona", r"c[oó]mo funciona", r"qu[eé] opciones", r"que opciones hay",
    r"como te uso", r"c[oó]mo te uso"
]) + r")\b"

# Cambios de modo (“ahora cambia a pagar”, etc.)
SWITCH  = r"\b(" + "|".join([
    r"(?:ahora|mejor|ya|ok)\s+(?:quiero|vamos a|cambia(?:r)?|pasemos a|c[aá]mbiame a|quiero ir a|vamos al|ahora s[íi])\s+(?:a\s+)?",
]) + r")(comprar|buscar|carro|carrito|pagar|devolver|reembolso|pedidos?|direcciones?|pagos?|rastrear)\b"

# Términos fuera de dominio
ABUSIVE = r"(?i)\b(?:pinch[ea]s?|pendej[oa]s?|idiot[ao]s?|imb[eé]cil(?:es)?|estupid[oa]s?|cabr[oó]n(?:es)?|hdp|ptm|mierd[ao]s?|chingad[a@]|chinga(?:r| tu madre)|chingatumadre|chingadamadre|vete a la verga|vete al diablo|vete a chingar|vete a la chingad[a@]|chingate|jodete|cagate|mu[eé]rete|mamon(?:es)?|culer[oa]s?|put[ií]n|put[ao]s?|putoncin|putarraco|putit[ao]s?|maric[oó]n(?:es)?|jot[oa]s?|lench[oa]s?|careverga[s]?|carechimba[s]?|mamahuevo|mama huevo|huev[oó]n(?:es)?|culo roto|traser[oó] apestoso)\b"

OFFTOP = r"\b(?:clima|pron[oó]stico|hora|reloj|d[oó]lar|tipo de cambio|pol[ií]tica|elecci[oó]n|partido|presidente|gobierno|senador(?:es)?|diputad[oa]s?|ministro[s]?|congreso|ley(?:es)?|corrupci[oó]n|noticia[s]?|periódico|revista|f[uú]tbol|futbol|soccer|b[aá]squet|basket|nba|béisbol|beisbol|tenis|box(?:eo)?|lucha|deporte[s]?|equipo|gol|torneo|mundial|champions|liga|resultado[s]?|marcador|tabla de posiciones|pel[ií]cula[s]?|cine|actor(?:es)?|actriz|serie[s]?|netflix|hbo|max|disney|plataforma|episodio[s]?|temporada[s]?|m[úu]sica|canci[oó]n|cantante[s]?|banda[s]?|grupo[s]?|rock|pop|reggaet[oó]n|rap|trap|corridos|balada|concierto[s]?|álbum|video musical|meme[s]?|chiste[s]?|cuento[s]?|historia[s]?|an[eé]cdota[s]?|poema[s]?|novela[s]?|autor(?:es)?|escritor(?:es)?|filosof[ií]a|psicolog[ií]a|matem[aá]ticas|ciencia[s]?|f[ií]sica|qu[ií]mica|biolog[ií]a|astronom[ií]a|universo|planeta[s]?|estrella[s]?|galaxia[s]?|alien(?:[ea]s)?|extraterrestre[s]?|ovni[s]?|ufo[s]?|nave espacial|nasa|cohete[s]?|misil(?:es)?|guerra|batalla[s]?|conflicto[s]?|ej[eé]rcito|soldad[oa]s?|arma[s]?|pistola[s]?|rifle[s]?|bomba[s]?|terrorismo|atentado|relig[ií]on(?:es)?|dios|jes[uú]s|cristo|biblia|al[aá]|mahoma|islam|jud[ií]o[s]?|cat[oó]lico[s]?|ate[oa]s?|rezar|orar|iglesia[s]?|templo[s]?|s[áa]tan|demonio[s]?|bruja[s]?|hechizo[s]?|magia|m[aá]gic[oa]s?|hor[óo]scopo[s]?|signo[s]? zodiacal(?:es)?|aries|tauro|g[eé]minis|c[aá]ncer|leo|virgo|libra|escorpio|sagitario|capricornio|acuario|piscis|tarot|c[aá]rt[aas]|vidente[s]?|predicci[oó]n(?:es)?|m[aá]s all[aá]|fantasma[s]?|esp[íi]ritu[s]?|duende[s]?|hada[s]?|mito[s]?|leyenda[s]?|drag[oó]n(?:es)?|criatura[s]?|pokemon|anime|manga|naruto|one piece|bleach|dragon ball|cosplay|otaku|waifu|husbando|juego[s]?|videojuego[s]?|xbox|playstation|ps5|ps4|switch|nintendo|steam|epic games|minecraft|roblox|fortnite|valorant|league of legends|lol|dota|counter strike|csgo|gta|fifa|call of duty|cod|pubg|apex|mobile legends|genshin impact|hogwarts legacy|among us|tiktok|facebook|instagram|whatsapp|twitter|x |threads|reddit|pinterest|snapchat|linkedin|youtuber[s]?|streamer[s]?|twitch|like[s]?|suscriptor(?:es)?|follower[s]?|seguidor(?:es)?|influencer[s]?|viral|tendencia[s]?|challenge[s]?|trend[s]?|baile[s]?|dance|salud mental|psiquiatr[aía]|depresi[oó]n|ansiedad|estr[eé]s|trauma[s]?|terapia[s]?|consulta[s]?|receta[s]?|embarazo|beb[eé]s?|familia|mam[aá]|pap[aá]|novi[oa]s?|pareja|espos[oa]s?|amig[oa]s?|compañer[oa]s?|vecin[oa]s?|trabaj[oó]s?|empleo[s]?|escuela|universidad(?:es)?|tarea[s]?|examen(?:es)?|curso[s]?|profesor(?:es)?|econom[ií]a|finanza[s]?|banco[s]?|pr[eé]stamo[s]?|hipoteca[s]?|ahorro[s]?|inversi[oó]n(?:es)?|bolsa de valores|cripto(?:moneda[s]?)?|bitcoin|ethereum|nft|blockchain|tr[aá]mite[s]?|documento[s]?|visa|pasaporte[s]?|ine|ife|seguro[s]?|licencia[s]?|acta de nacimiento|historia universal|prehistoria|edad media|renacimiento|arqueolog[oa]s?|descubrimiento[s]?|invenci[oó]n(?:es)?|playa[s]?|oc[eé]ano[s]?|montaña[s]?|bosque[s]?|selva|desierto|ciudad(?:es)?|pueblo[s]?|colonia[s]?|restaurante[s]?|caf[eé]|bar(?:es)?|cantina[s]?|discoteca[s]?|viaje[s]?|turismo|hotel(?:es)?|airbnb|avión(?:es)?|vuelo[s]?|tren(?:es)?|camión(?:es)?|autob[uú]s(?:es)?|uber|didi|taxi[s]?|gasolina|petr[oó]leo|electricidad|energ[ií]a|naturaleza|animal(?:es)?)\b"


ORDER_ID_RE = r"\b\d{3}-\d{7}-\d{7}\b"

# =========================
# Intents ampliados
# =========================

INTENTS = {
   # Globales
   "EXIT":       re.compile(SALIR, re.I),
   "BACK":       re.compile(ATRAS, re.I),
   "HELP":       re.compile(AYUDA, re.I),
   "SWITCH":     re.compile(SWITCH, re.I),
   "ABUSIVE":    re.compile(ABUSIVE, re.I),
   "OFF_TOPIC":  re.compile(OFFTOP, re.I),

   # Navegación / compras
   "VIEW_CART":  re.compile(r"\b(mi\s+carrito|ver\s+carrito|carrito|carro\s+de\s+compras|mi\s+carro|cesta|canasta|basket)\b", re.I),
   "PAY":        re.compile(r"\b(pagar|checkout|ir a caja|finalizar compra|pasar a pagar|comprar ahora)\b", re.I),

   # “Buscar” muy amplio (necesito/quiero/busco/ocupo/enséñame/muéstrame/recomiéndame/quisiera/tienes/traigo ganas de…)
   "SEARCH":     re.compile(
       r"\b("
       r"buscar|busco|ocupo|ocupar|necesito|requiero|quiero|quisiera|"
       r"mues?trame|ense(?:n|ñ)ame|recom[ií]endame|recomiend[aá]me|"
       r"tienes?|que tienes de|traigo ganas de|me late|me gustar[ií]a ver|"
       r"quiero ver|m[uú]estra|ense(?:n|ñ)a|sugi[e|e]re|sugerencias?"
       r")\b.*",
       re.I),

    # Selección por índice (ej: "el 2", "quiero el número 3")
    "SELECT_N": re.compile(
        r"^(?:el|la|los|las)?\s*(?:n[uú]mero|num|#)?\s*(?P<idx>\d+)\b", re.I),

    # Cantidades
    "QTY_SET": re.compile(
        r"(?:"
        r"pon(?:me|le)?|pone|coloca|mete|deja|quiero|va a ser|me llevo|dame|asigna|configura|setea|"
        r"cambia(?:r)? a|ajusta|define|actualiza|establece|déjame en|fija|"
        r"ser[aá]|voy a llevarme|necesito|requiero"
        r")\s+(.*)", re.I),

    "QTY_ADD": re.compile(
        r"(?:"
        r"agrega|añade|a[nñ]ade|suma|sube|s[úu]bele|incrementa|métele|sumale|"
        r"pon(?:me|le)? m[aá]s|añ[aá]dele|agr[eé]gale|coloca otro|mete otro|"
        r"agregar otro|añadir otro|quiero m[aá]s|más piezas|más unidades|échale más|"
        r"échame otro|agrega uno más|súmale otro"
        r")\s+(.*)", re.I),

    "QTY_SUB": re.compile(
        r"(?:"
        r"quita|resta|baja|b[aá]jale|menos|r[ée]stale|disminuye|elimina|saca|"
        r"borra uno|quita uno|qu[ií]tale|descarta|saca uno|quítame|déjalo en menos|reduce|"
        r"quita una pieza|quita una unidad|quítame un producto"
        r")\s+(.*)", re.I),

    # Confirmación y negación
    "CONFIRM": re.compile(AFIRMAR, re.I),
    "DENY": re.compile(NEGAR, re.I),

    # Carrito
    "CART_CLEAR": re.compile(
        r"\b("
        r"vaciar carrito|vaciar mi carro|vaciar mi carrito|borra todo|quita todo|limpia carrito|elimina todo|"
        r"limpia la cesta|vacía la bolsa|borra mi carrito|deja el carrito vacío|"
        r"quitar todo lo del carrito|saca todo|resetear carrito|reinicia carrito"
        r")\b", re.I),

    "CART_REMOVE_INDEX": re.compile(
        r"\b("
        r"elimina(?:r)?|quitar|borrar|remueve|remover|descarta|descartar|saca|sacar|borra|borrar|quita|elimina del carrito"
        r")\b.*?(?:el|la|los|las)?\s*(?P<idx>\d+)\b", re.I),

    "CART_SET_QTY_IDX": re.compile(
        r"\b("
        r"cambia(?:r)? cantidad|pon|pone|ponle|deja|dejar|ajusta|"
        r"modifica cantidad|actualiza cantidad|fija cantidad|establece|"
        r"cambia el número|setea cantidad|configura cantidad|déjalo en"
        r")\b\s+(?P<qty_text>.+?)\s+(?:al|a la|del|de la)\s+(?P<idx>\d+)\b", re.I),

    "CART_ADD_QTY_IDX": re.compile(
        r"\b("
        r"agrega|añade|anade|suma|sube|s[úu]bele|m[aá]s|sumale|"
        r"añ[aá]dele|agr[eé]gale|métele|ponle otro|échale otro|mete uno más|"
        r"añadir otro|agregar otro|sumar otro"
        r")\b\s+(?P<qty_text>.+?)\s+(?:al|a la|del|de la)\s+(?P<idx>\d+)\b", re.I),

    "CART_SUB_QTY_IDX": re.compile(
        r"\b("
        r"quita|resta|baja|b[aá]jale|menos|r[ée]stale|disminuye|saca|elimina|"
        r"quítale uno|borra uno|reduce cantidad|quita cantidad|déjalo en menos"
        r")\b\s+(?P<qty_text>.+?)\s+(?:al|a la|del|de la)\s+(?P<idx>\d+)\b", re.I),

   # Devolución & reembolso
   "DEV_START":         re.compile(
       r"\b("
       r"devolver|devoluci[oó]n|cambio|cambiar por|regresar|"
       r"no me (?:sirve|qued[óo]|quedo|gust[oó])|muy (?:grande|chico|peque[nñ]o)|"
       r"me equivoqu[eé] (?:de talla|al pedir)|defectuoso|no funciona|fall[ao]|da[nñ]ado|golpeado"
       r")\b", re.I),
   "REFUND_STATUS":     re.compile(
       r"\b("
       r"reembolso|reintegro|devoluci[oó]n de dinero|estatus del reembolso|"
       r"cuando (?:me )?(?:depositan|devuelven|cae el dinero|me cae)|"
       r"me regresan mi dinero|estado del reembolso"
       r")\b", re.I),

   "ORDER_ID_OR_RECENT": re.compile(rf"({ORDER_ID_RE}|el mas reciente|el más reciente|ultimo|último|mas reciente|más reciente)", re.I),
   "DEV_REASON":        re.compile(
       r"\b("
       r"no es lo que ped[ií]|dañad[oa]|golpead[oa]|incompleto|defectuoso|no funciona|"
       r"me equivoqu[eé]|tarde|no me gust[óo]|muy (?:grande|chico|peque[nñ]o)|otro|otra cosa|empaque abierto"
       r")\b", re.I),
   "DEV_METHOD":        re.compile(r"\b(etiqueta|paqueter[ií]a|punto de entrega|drop ?off|tienda|sucursal|recolecci[oó]n)\b", re.I),

   # Admin (menús)
   "ADMIN_DIR":         re.compile(r"\b(direcciones?|domicilios?|direcci[oó]n de env[ií]o|domicilio de entrega)\b", re.I),
   "ADMIN_PAGO":        re.compile(r"\b(pagos?|tarjetas?|m[eé]todo de pago|metodo de pago|forma de pago)\b", re.I),

   # Checkout extra
   "PAY_USE_INDEX":     re.compile(r"\b(?:usar|metod[oó]|m[eé]todo|tarjeta)\s+(?P<idx>\d+)\b", re.I),
   "PAY_CHANGE":        re.compile(r"\b(cambiar\s+(?:metod[oó]|m[eé]todo|tarjeta)|otr[ao]\s+(?:metod[oó]|m[eé]todo|pago|tarjeta))\b", re.I),
   "PROCEED_PAY":       re.compile(r"\b(proceder (?:al|a) pago|continuar (?:al|con el) pago|ir a pagar|seguir a pagar)\b", re.I),
   "CONFIRM_PAY":       re.compile(r"\b(realiza(?:r)? tu pedido(?: y paga)?|realiza tu pedido y paga|pagar ahora|confirmar compra)\b", re.I),
   "PAY_ADDR_CHANGE":   re.compile(r"\b(cambiar|modificar|editar)\s+(?:direccion|dirección|domicilio)(?:\s+de\s+env[ií]o)?\b|\botra\s+(?:direccion|dirección)\b", re.I),
   "PAY_ADDR_USE_INDEX":re.compile(r"\b(?:usar|direccion|dirección)\s+(?P<idx>\d+)\b", re.I),
   "ADDR_WORD":         re.compile(r"\b(direccion|dirección|direcciones|domicilio(?:s)?)\b", re.I),

   # Admin extras (acciones)
   "ADMIN_DIR_ENTER": re.compile(r"\b(direcciones?|domicilios?)\b", re.I),
   "ADMIN_PAGO_ENTER":re.compile(r"\b(pagos?|tarjetas?|metodo de pago|m[eé]todo de pago)\b", re.I),
   "ADD_WORD":   re.compile(r"\b(agregar tarjeta|añadir|anadir|nueva|registrar|dar de alta|sumar|meter)\b", re.I),
   "DEL_IDX":    re.compile(r"\b(elimina(?:r)?|quitar|borrar|remueve|elimina)\b.*?(?P<idx>\d+)", re.I),
   "SETDEF_IDX": re.compile(r"\b(predeterminad[ao]|principal|pordefecto|por defecto|usar|poner(?:la)?\s+como\s+predeterminad[ao])\b.*?(?P<idx>\d+)", re.I),
   "BRAND":      re.compile(r"\b(visa|master ?card|mastercard|american ?express|americanexpress|amex|carnet)\b", re.I),
   "LAST4":      re.compile(r"\b(\d{4})\b"),

   # Pedidos (historial y detalle)
   "ORDERS_ENTER":  re.compile(r"\b(mis pedidos|ver pedidos|historial de pedidos|historial|pedidos)\b", re.I),
   "ORDER_BY_ID":   re.compile(rf"{ORDER_ID_RE}", re.I),

   # Cancelación y recepción de devolución
   "CANCEL_START":        re.compile(r"\b(cancelar(?: pedido)?|anular|cancela(?:r)? lo|echa(?:r)? pa'? tr[aá]s|ya no lo quiero|ya fue)\b", re.I),
   "RETURN_MARK_RECEIVED":re.compile(r"\b(marcar|ya)\s+(?:devolucion|devolución)\s*(?:#?)(?P<rid>\d+)?\s*(?:recibida|entregada)\b", re.I),

   # Rastreo (solo liga)
   "TRACK_ENTER": re.compile(
       r"\b("
       r"rastrear|rastreo|seguimiento|ver env[ií]o|d[oó]nde va|por d[oó]nde va|"
       r"mi paquete|estado del env[ií]o|track|tracking|rastrea|en d[oó]nde viene"
       r")\b", re.I),

   # Saludos (no disparan SEARCH si los chequeas antes)
   "GREET": re.compile(
       r"\b("
       r"hola+|holi+s?|holis|buen[oa]s?\s*(d[ií]as|tardes|noches)?|"
       r"q(?:u[eé])?\s+(tal|onda)|qu[eé]\s+(tal|onda)|hey+|hi+|hello+|"
       r"buen\s*dia|buen dia"
       r")\b", re.I),

   # Smalltalk corto (ok, gracias, jaja…)
   "SMALLTALK": re.compile(
       r"\b("
       r"gracias+|grax|lmao|grx|thx|ty|ok+|oki+s?|okey|va+le|aja+|jaja+|jeje+|xd+|"
       r"saludos+|perfecto|entendido|de acuerdo|deacuerdo|nice|cool"
       r")\b", re.I),

   # Nombre del usuario
   "SET_NAME": re.compile(
       r"\b(?:me\s+llamo|soy|mi\s+nombre\s+es|me\s+dicen|ll[aá]mame|ll[aá]mame)\s+([A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)\b", re.I),
}