"""
Analizador Semántico — Lenguaje de Gestión de Proyectos
========================================================
Implementado según el Manual del Lenguaje (Análisis Semántico).

REGLAS SEMÁNTICAS
─────────────────
Usuarios:
  R1  — Un usuario no puede registrarse dos veces (E001)
  R2  — Un usuario debe existir antes de operar (E002)
  R3  — Un usuario debe tener sesión activa para crear tareas (E003)
  R4  — Los roles ROL.COORD/ROL.MIEM solo se asignan a usuarios existentes (E002)

Grupos:
  R5  — No pueden existir dos grupos con el mismo nombre (E004)
  R6  — Un usuario solo puede asignarse a un grupo existente (E005)
  R7  — Un grupo debe existir antes de asignarle tareas (E005)

Tareas:
  R8  — No pueden existir dos tareas con el mismo nombre en el mismo grupo (E006)
  R9  — Una tarea solo puede asignarse a un usuario existente (E002)
  R10 — Una subtarea debe pertenecer a una tarea padre existente (E008)
  R11 — No se puede dividir una tarea que ya tiene subtareas (E009)
  R12 — Una tarea no puede autoevaluarse si no está asignada al usuario activo (E010)
  R13 — La calificación debe ser un número entre 0 y 100 (E011)

Fechas:
  R14 — La fecha límite no puede ser anterior a la fecha de creación (E012)
  R15 — En tareas recurrentes, HASTA debe ser posterior a hoy (E012)

Listas y vistas:
  R16 — No pueden existir dos listas con el mismo título (E013)
  R17 — Una lista debe existir antes de agregarle tareas (E014)
  R18 — No se puede crear una vista con un nombre ya utilizado (E015)
  R19 — Las condiciones de filtro deben referirse a prioridades/estados existentes

Notificaciones:
  R20 — El destinatario de una notificación debe ser un usuario existente (E002)
  R21 — La tarea referenciada en SUSCRIBIR debe existir (E007)

CÓDIGOS DE ERROR
────────────────
  E001 — USUARIO_DUPLICADO
  E002 — USUARIO_NO_EXISTE
  E003 — USUARIO_NO_AUTENTICADO
  E004 — GRUPO_DUPLICADO
  E005 — GRUPO_NO_EXISTE
  E006 — TAREA_DUPLICADA
  E007 — TAREA_NO_EXISTE
  E008 — SUBTAREA_SIN_PADRE
  E009 — TAREA_YA_DIVIDIDA
  E010 — AUTOEVAL_NO_PERMITIDA
  E011 — CALIFICACION_FUERA_RANGO
  E012 — FECHA_INVALIDA_RELACION
  E013 — LISTA_DUPLICADA
  E014 — LISTA_NO_EXISTE
  E015 — VISTA_DUPLICADA
  E016 — CONDICION_INVALIDA
"""

from Sintactico import AnalizadorSintactico, Nodo
import datetime


# ─────────────────────────────────────────────────────────────
# ERROR SEMÁNTICO
# ─────────────────────────────────────────────────────────────

class ErrorSemantico(Exception):
    """
    Error semántico con código, regla violada, sentencia y línea.
    Detiene el análisis inmediatamente (como pide el manual).
    """
    def __init__(self, codigo, regla, mensaje, sentencia="", linea=None):
        super().__init__(mensaje)
        self.codigo    = codigo      # Ej. "E002"
        self.regla     = regla       # Ej. "R9"
        self.sentencia = sentencia   # Ej. "ASIG.TAR(Modelo ER) ASIG.USR(maria)"
        self.linea     = linea
        # Mensaje formateado para mostrar al usuario
        linea_str = f"Línea {linea}: " if linea else ""
        self.mensaje = (
            f"{linea_str}[{codigo}] {mensaje}"
        )
        self.detalle = (
            f"Regla violada: {regla} | "
            f"Sentencia: {sentencia}"
        ) if sentencia else f"Regla violada: {regla}"


# ─────────────────────────────────────────────────────────────
# TABLA DE SÍMBOLOS
# ─────────────────────────────────────────────────────────────

class TablaSimbolos:
    """
    Tabla de símbolos construida dinámicamente durante el análisis.

    Campos por entrada:
        identificador  — Nombre único
        categoria      — USUARIO | GRUPO | TAREA | LISTA | VISTA | MODULO | BIBLIOTECA
        tipo           — Subtipo: ROL.COORD, ROL.MIEM, TAREA.GRP, TAREA.IND,
                         SUBTAREA, RECURRENTE/xxx, VISTA/filtro, IMPORT, BIB
        valor          — Nombre completo (usuarios) u otro valor asociado
        estado         — Estado semántico actual (PENDIENTE por defecto)
        sesion         — activa | inactiva (solo usuarios)
        prioridad      — PRI.URG | PRI.ALT | PRI.MED | PRI.BAJ | —
        asignado_a     — Identificador del usuario asignado
        grupo          — Grupo al que pertenece la tarea
        fecha_limite   — Fecha límite declarada
        descripcion    — Descripción declarada
        etiquetas      — Lista de etiquetas
        subtareas      — Lista de subtareas hijas (para tareas padre)
        suscriptores   — Usuarios suscritos
        miembros       — Miembros del grupo
        tareas_lista   — Tareas contenidas en una lista
        linea          — Línea de declaración
        contexto       — Contexto de pertenencia (grupo para tareas)
    """

    def __init__(self):
        self._tabla = {}   # identificador → dict
        self._log   = []   # historial de acciones paso a paso

    # ── Operaciones ──────────────────────────────────────────

    def agregar(self, identificador, categoria, tipo="—",
                linea=None, contexto="—", **extra):
        entrada = {
            "identificador": identificador,
            "categoria":     categoria,
            "tipo":          tipo,
            "valor":         extra.get("valor",        "—"),
            "estado":        extra.get("estado",       "PENDIENTE"),
            "sesion":        extra.get("sesion",       "inactiva"),
            "prioridad":     extra.get("prioridad",    "—"),
            "asignado_a":    extra.get("asignado_a",   "—"),
            "grupo":         extra.get("grupo",        "—"),
            "fecha_limite":  extra.get("fecha_limite", "—"),
            "descripcion":   extra.get("descripcion",  "—"),
            "etiquetas":     extra.get("etiquetas",    []),
            "subtareas":     extra.get("subtareas",    []),
            "suscriptores":  extra.get("suscriptores", []),
            "miembros":      extra.get("miembros",     []),
            "tareas_lista":  extra.get("tareas_lista", []),
            "linea":         linea or 0,
            "contexto":      contexto,
        }
        self._tabla[identificador] = entrada
        self._log.append({
            "accion":  "AGREGAR",
            "detalle": (f"[{categoria}] '{identificador}' "
                        f"tipo={tipo}"
                        f"{', línea=' + str(linea) if linea else ''}"),
            "linea":   linea or 0,
            "paso":    len(self._log) + 1,
        })

    def actualizar(self, identificador, campo, valor, razon="", linea=None):
        if identificador not in self._tabla:
            return
        anterior = self._tabla[identificador].get(campo, "—")
        self._tabla[identificador][campo] = valor
        self._log.append({
            "accion":  "ACTUALIZAR",
            "detalle": (f"'{identificador}'.{campo}: "
                        f"'{anterior}' → '{valor}'"
                        f"{' (' + razon + ')' if razon else ''}"),
            "linea":   linea or 0,
            "paso":    len(self._log) + 1,
        })

    def validar(self, identificador, campo, descripcion="", linea=None):
        """Registra una validación en el log (verificación que resultó OK)."""
        self._log.append({
            "accion":  "VALIDAR",
            "detalle": (f"'{identificador}' — {descripcion}"
                        if descripcion else f"'{identificador}' OK"),
            "linea":   linea or 0,
            "paso":    len(self._log) + 1,
        })

    def existe(self, identificador):
        return identificador in self._tabla

    def obtener(self, identificador):
        return self._tabla.get(identificador)

    def por_categoria(self, categoria):
        return [e for e in self._tabla.values() if e["categoria"] == categoria]

    def usuario_activo(self):
        """Devuelve el identificador del primer usuario con sesión activa."""
        for e in self._tabla.values():
            if e["categoria"] == "USUARIO" and e.get("sesion") == "activa":
                return e["identificador"]
        return None

    def a_lista(self):
        return list(self._tabla.values())

    def log(self):
        return self._log

    def imprimir(self):
        fmt = "{:<28} {:<12} {:<16} {:<12} {:<10} {:<14} {:<16} {:<8} {}"
        cab = fmt.format("IDENTIFICADOR","CATEGORÍA","TIPO","ESTADO",
                         "PRIORIDAD","ASIGNADO_A","FECHA_LÍMITE","SESIÓN","LÍNEA")
        sep = "─" * 130
        print(f"\n{sep}\n  TABLA DE SÍMBOLOS\n{sep}")
        print(cab)
        print(sep)
        for e in self._tabla.values():
            print(fmt.format(
                str(e["identificador"])[:27],
                str(e["categoria"])[:11],
                str(e["tipo"])[:15],
                str(e["estado"])[:11],
                str(e["prioridad"])[:9],
                str(e["asignado_a"])[:13],
                str(e["fecha_limite"])[:15],
                str(e.get("sesion","—"))[:7],
                str(e["linea"]),
            ))
        print(sep)


# ─────────────────────────────────────────────────────────────
# ANALIZADOR SEMÁNTICO
# ─────────────────────────────────────────────────────────────

class AnalizadorSemantico:

    HOY = datetime.date.today()

    # Prioridades y estados válidos del lenguaje
    PRIORIDADES_VALIDAS = {"PRI.URG", "PRI.ALT", "PRI.MED", "PRI.BAJ"}
    ESTADOS_VALIDOS     = {"EST.PEN", "EST.ACT", "EST.REV",
                           "EST.COR", "EST.APROB", "EST.RECH", "EST.FIN"}

    def __init__(self):
        self.sint  = AnalizadorSintactico()
        self.tabla = TablaSimbolos()

    # ═══════════════════════════════════════════════════════════
    # PUNTO DE ENTRADA
    # ═══════════════════════════════════════════════════════════

    def analizar(self, texto):
        """
        Ejecuta léxico → sintáctico → semántico.
        Devuelve (tabla, log, exito, mensaje, detalle_error).
        """
        self.tabla = TablaSimbolos()

        # ── Fases 1 y 2 ──────────────────────────────────────
        arbol, _, ok_sint, msg_sint = self.sint.analizar(texto)
        if not ok_sint:
            return self.tabla, [], False, f"[Sintáctico] {msg_sint}", ""

        # ── Fase 3: Semántica ─────────────────────────────────
        try:
            self._recorrer_programa(arbol)
            self._imprimir_ok()
            return (self.tabla, self.tabla.log(),
                    True, "Análisis semántico correcto", "")
        except ErrorSemantico as e:
            print(f"\n❌ ERROR SEMÁNTICO\n"
                  f"   Código   : {e.codigo}\n"
                  f"   Mensaje  : {e.mensaje}\n"
                  f"   {e.detalle}\n")
            return (self.tabla, self.tabla.log(),
                    False, e.mensaje, e.detalle)

    # ═══════════════════════════════════════════════════════════
    # RECORRIDO DEL ÁRBOL SINTÁCTICO
    # ═══════════════════════════════════════════════════════════

    def _recorrer_programa(self, raiz):
        """Paso 2 del flujo: recorre el AST sentencia por sentencia."""
        for sent in raiz.hijos:
            self._despachar(sent)

    DISPATCH = {
        "SENT_REG_USUARIO":     "_reg_usuario",
        "SENT_CREAR_USUARIO":   "_reg_usuario",
        "SENT_INGRESO_USUARIO": "_ing_usuario",
        "SENT_BUSCAR_USUARIO":  "_bus_usuario",
        "SENT_CREAR_GRUPO":     "_cre_grupo",
        "SENT_ASIGNAR_USUARIO": "_asig_usuario_solo",
        "SENT_CREAR_TAREA":     "_cre_tarea",
        "SENT_ASIGNAR_TAREA":   "_asig_tarea",
        "SENT_DIVIDIR_TAREA":   "_div_tarea",
        "SENT_CREAR_SUBTAREA":  "_cre_subtarea",
        "SENT_TAREA_RECURRENTE":"_rec_tarea",
        "SENT_VER_TAREAS_IND":  "_ignorar",
        "SENT_VER_AVANCE":      "_ver_avan",
        "SENT_AUTOEVALUAR":     "_autoevaluar",
        "SENT_CALIFICAR":       "_calificar",
        "SENT_ETIQUETAR":       "_etiquetar",
        "SENT_FILTRO":          "_filtro",
        "SENT_VER_VISTA":       "_ver_vista",
        "SENT_NOTIF_CUANDO":    "_notif_cuando",
        "SENT_NOTIF_RECORDAR":  "_notif_recordar",
        "SENT_SUSCRIBIR":       "_suscribir",
        "SENT_CREAR_LISTA":     "_cre_lista",
        "SENT_AGREGAR_LISTA":   "_ag_lista",
        "SENT_VER_LISTA":       "_ver_lista",
        "SENT_ELIMINAR_LISTA":  "_elim_lista",
        "SENT_COMENTARIO":      "_comentario",
        "SENT_ENVIAR_MENSAJE":  "_env_msg",
        "SENT_ENVIAR_ENLACE":   "_env_enl",
        "SENT_VER_MENSAJES":    "_ignorar",
        "SENT_IMPORTAR":        "_importar",
        "SENT_EXPORTAR":        "_exportar",
        "SENT_USAR_BIBLIOTECA": "_usar_bib",
    }

    def _despachar(self, nodo):
        metodo = self.DISPATCH.get(nodo.etiqueta)
        if metodo:
            getattr(self, metodo)(nodo)
        # SENT_SALIR, SENT_MENU, etc. sin reglas semánticas: se ignoran

    def _ignorar(self, nodo):
        pass

    # ═══════════════════════════════════════════════════════════
    # HELPERS DE EXTRACCIÓN DEL ÁRBOL
    # ═══════════════════════════════════════════════════════════

    def _hijo(self, nodo, etiqueta):
        for h in nodo.hijos:
            if h.etiqueta == etiqueta:
                return h
        return None

    def _valor_hijo(self, nodo, etiqueta):
        h = self._hijo(nodo, etiqueta)
        if h and h.hijos:
            return h.hijos[0].etiqueta.strip('"').strip("'")
        return None

    def _parse_fecha(self, texto):
        try:
            return datetime.date.fromisoformat(texto)
        except Exception:
            return None

    def _nombre_sentencia(self, nodo):
        """Reconstruye un nombre legible de la sentencia para el log de error."""
        partes = []
        for h in nodo.hijos:
            if not h.hijos:
                partes.append(h.etiqueta)
            else:
                partes.append(h.etiqueta + "(" +
                              ", ".join(hh.etiqueta for hh in h.hijos) + ")")
        return " ".join(partes[:5])

    # ═══════════════════════════════════════════════════════════
    # VERIFICACIONES REUTILIZABLES (con código y regla)
    # ═══════════════════════════════════════════════════════════

    def _chk_usuario_existe(self, nombre, sentencia="", linea=None):
        """R2/R4/R9/R20 — El usuario debe existir."""
        if not nombre or nombre == "—":
            return
        if not self.tabla.existe(nombre):
            raise ErrorSemantico(
                "E002", "R2",
                f"Usuario '{nombre}' no ha sido registrado — use REG.USR primero",
                sentencia, linea
            )
        self.tabla.validar(nombre, "existe", f"usuario existe ✓", linea)

    def _chk_sesion_activa(self, sentencia="", linea=None):
        """R3 — Debe haber un usuario con sesión activa."""
        if not self.tabla.usuario_activo():
            raise ErrorSemantico(
                "E003", "R3",
                "No hay usuario con sesión activa — use ING.USR antes de esta operación",
                sentencia, linea
            )

    def _chk_grupo_existe(self, nombre, sentencia="", linea=None):
        """R6/R7 — El grupo debe existir."""
        if not nombre or nombre == "—":
            return
        entrada = self.tabla.obtener(nombre)
        if not entrada or entrada["categoria"] != "GRUPO":
            raise ErrorSemantico(
                "E005", "R6",
                f"Grupo '{nombre}' no existe — use CRE.GRP primero",
                sentencia, linea
            )
        self.tabla.validar(nombre, "existe", "grupo existe ✓", linea)

    def _chk_tarea_existe(self, nombre, sentencia="", linea=None):
        """R8/R10/R11/R12 — La tarea debe existir."""
        if not nombre or nombre == "—":
            return
        entrada = self.tabla.obtener(nombre)
        if not entrada or entrada["categoria"] != "TAREA":
            raise ErrorSemantico(
                "E007", "R8",
                f"Tarea '{nombre}' no declarada — use CRE.TAR primero",
                sentencia, linea
            )
        self.tabla.validar(nombre, "existe", "tarea existe ✓", linea)

    def _chk_lista_existe(self, nombre, sentencia="", linea=None):
        """R17 — La lista debe existir."""
        if not nombre or nombre == "—":
            return
        entrada = self.tabla.obtener(nombre)
        if not entrada or entrada["categoria"] != "LISTA":
            raise ErrorSemantico(
                "E014", "R17",
                f"Lista '{nombre}' no existe — use CRE.LIS primero",
                sentencia, linea
            )
        self.tabla.validar(nombre, "existe", "lista existe ✓", linea)

    def _chk_fecha_valida(self, fecha_str, nombre_tarea, sentencia="", linea=None):
        """R14/R15 — La fecha no puede ser anterior a hoy."""
        if not fecha_str or fecha_str in ("—", "PROX.LUN", "FIN.MES",
                                           "FIN.SEM", "INI.MES", "INI.SEM",
                                           "HOY"):
            return  # fechas relativas no se validan temporalmente
        fecha = self._parse_fecha(fecha_str)
        if fecha and fecha < self.HOY:
            raise ErrorSemantico(
                "E012", "R14/R15",
                f"Fecha '{fecha_str}' de '{nombre_tarea}' es anterior a hoy "
                f"({self.HOY}) — la tarea ya habría vencido",
                sentencia, linea
            )

    # ═══════════════════════════════════════════════════════════
    # PASO 1: INICIALIZACIÓN (implícita al crear TablaSimbolos)
    # ═══════════════════════════════════════════════════════════
    # La tabla inicia vacía, usuario activo = None, contexto = global.

    # ═══════════════════════════════════════════════════════════
    # PASO 3: VALIDACIÓN POR TIPO DE SENTENCIA
    # ═══════════════════════════════════════════════════════════

    # ── Usuarios ─────────────────────────────────────────────

    def _reg_usuario(self, nodo):
        """
        REG.USR / CRE.USR
        R1 — no duplicar usuario.
        Agrega el usuario a la tabla con su rol.
        """
        nombre = self._valor_hijo(nodo, "USUARIO")
        if not nombre:
            return
        sent = self._nombre_sentencia(nodo)

        # R1 — No redeclaración
        if self.tabla.existe(nombre):
            e = self.tabla.obtener(nombre)
            raise ErrorSemantico(
                "E001", "R1",
                f"Usuario '{nombre}' ya fue registrado (línea {e['linea']}) "
                f"— no se puede registrar dos veces",
                sent
            )

        # Extraer rol
        rol = "ROL.MIEM"
        for h in nodo.hijos:
            if h.etiqueta in ("ROL.COORD", "ROL.MIEM"):
                rol = h.etiqueta

        nombre_completo = self._valor_hijo(nodo, "NOMBRE_COMPLETO") or "—"

        self.tabla.agregar(
            nombre, "USUARIO", tipo=rol,
            valor=nombre_completo,
            sesion="inactiva",
        )

    def _ing_usuario(self, nodo):
        """
        ING.USR
        R2 — usuario debe existir.
        Activa la sesión del usuario.
        """
        nombre = self._valor_hijo(nodo, "USUARIO")
        sent   = self._nombre_sentencia(nodo)
        self._chk_usuario_existe(nombre, sent)
        self.tabla.actualizar(nombre, "sesion", "activa",
                              "ING.USR — sesión iniciada")

    def _bus_usuario(self, nodo):
        """BUS.USR — sin reglas semánticas estrictas (búsqueda libre)."""
        pass

    def _asig_usuario_solo(self, nodo):
        """ASIG.USR como sentencia independiente — R2."""
        nombre = self._valor_hijo(nodo, "USUARIO")
        self._chk_usuario_existe(nombre, self._nombre_sentencia(nodo))

    # ── Grupos ───────────────────────────────────────────────

    def _cre_grupo(self, nodo):
        """
        CRE.GRP
        R5 — no duplicar grupo.
        R6 — usuarios asignados deben existir.
        """
        nombre = self._valor_hijo(nodo, "NOMBRE_GRUPO")
        if not nombre:
            return
        sent = self._nombre_sentencia(nodo)

        # R5 — no duplicar
        if self.tabla.existe(nombre):
            e = self.tabla.obtener(nombre)
            raise ErrorSemantico(
                "E004", "R5",
                f"Grupo '{nombre}' ya fue declarado (línea {e['linea']})",
                sent
            )

        miembros = []

        # Verificar usuarios en ASIG.USR dentro del grupo
        asig = self._hijo(nodo, "ASIG_USUARIO")
        if asig:
            usr = self._valor_hijo(asig, "USUARIO")
            # R6
            self._chk_usuario_existe(usr, sent)
            miembros.append(usr)

        self.tabla.agregar(
            nombre, "GRUPO", tipo="GRP",
            miembros=miembros,
        )

        if miembros:
            self.tabla.actualizar(nombre, "asignado_a", miembros[0],
                                  "coordinador del grupo")

    # ── Tareas ───────────────────────────────────────────────

    def _cre_tarea(self, nodo):
        """
        CRE.TAR / CRE.TAR.GRP / CRE.TAR.IND
        R3  — debe haber sesión activa.
        R8  — no duplicar tarea.
        R14 — fecha válida.
        """
        nombre = self._valor_hijo(nodo, "NOMBRE_TAREA")
        if not nombre:
            return
        sent = self._nombre_sentencia(nodo)

        # R3 — sesión activa
        self._chk_sesion_activa(sent)

        # R8 — no duplicar
        if self.tabla.existe(nombre):
            e = self.tabla.obtener(nombre)
            raise ErrorSemantico(
                "E006", "R8",
                f"Tarea '{nombre}' ya fue declarada (línea {e['linea']}) "
                f"— use un nombre distinto",
                sent
            )

        # Determinar subtipo
        tipo = "TAREA"
        for h in nodo.hijos:
            if h.etiqueta == "CRE.TAR.GRP": tipo = "TAREA.GRP"; break
            if h.etiqueta == "CRE.TAR.IND": tipo = "TAREA.IND"; break

        # Extraer modificadores
        prioridad   = "—"
        fecha_lim   = "—"
        descripcion = "—"

        for h in nodo.hijos:
            if h.etiqueta == "PRIORIDAD" and h.hijos:
                prioridad = h.hijos[0].etiqueta
            if h.etiqueta == "FECHA_MOD":
                ef = self._hijo(h, "EXPR_FECHA")
                if ef and ef.hijos:
                    fecha_lim = ef.hijos[0].etiqueta
            if h.etiqueta == "DESCRIPCION":
                dn = self._hijo(h, "TEXTO")
                if dn and dn.hijos:
                    descripcion = dn.hijos[0].etiqueta
            # R9 — usuario en modificador ASIG.USR
            if h.etiqueta == "ASIG_USUARIO":
                usr = self._valor_hijo(h, "USUARIO")
                self._chk_usuario_existe(usr, sent)

        # R14 — fecha válida
        self._chk_fecha_valida(fecha_lim, nombre, sent)

        # Contexto: grupo activo si existe
        usuario_act = self.tabla.usuario_activo()
        grupo_ctx   = "—"
        # Buscar el grupo al que está asignado el usuario activo
        for g in self.tabla.por_categoria("GRUPO"):
            if usuario_act in g.get("miembros", []) or g.get("asignado_a") == usuario_act:
                grupo_ctx = g["identificador"]
                break

        self.tabla.agregar(
            nombre, "TAREA", tipo=tipo,
            prioridad=prioridad,
            fecha_limite=fecha_lim,
            descripcion=descripcion,
            contexto=grupo_ctx,
        )

    def _asig_tarea(self, nodo):
        """
        ASIG.TAR
        R8  — tarea debe existir.
        R9  — usuario debe existir.
        """
        nombre = self._valor_hijo(nodo, "NOMBRE_TAREA")
        sent   = self._nombre_sentencia(nodo)

        self._chk_tarea_existe(nombre, sent)

        asig = self._hijo(nodo, "ASIG_USUARIO")
        if asig:
            usr = self._valor_hijo(asig, "USUARIO")
            # R9
            self._chk_usuario_existe(usr, sent)
            self.tabla.actualizar(nombre, "asignado_a", usr, "ASIG.TAR")

    def _div_tarea(self, nodo):
        """
        DIV.TAR
        R10/R11 — tarea padre debe existir y no tener subtareas previas.
        """
        nombre = self._valor_hijo(nodo, "NOMBRE_TAREA")
        sent   = self._nombre_sentencia(nodo)

        # R10 — tarea padre debe existir
        self._chk_tarea_existe(nombre, sent)

        entrada = self.tabla.obtener(nombre)

        # R11 — no puede ya tener subtareas
        if entrada.get("subtareas"):
            raise ErrorSemantico(
                "E009", "R11",
                f"Tarea '{nombre}' ya tiene subtareas {entrada['subtareas']} "
                f"— no se puede dividir de nuevo",
                sent
            )

        nuevas_subs = []
        for h in nodo.hijos:
            if h.etiqueta == "SUBTAREA":
                sub_nom = self._valor_hijo(h, "NOMBRE")
                if sub_nom:
                    if self.tabla.existe(sub_nom):
                        raise ErrorSemantico(
                            "E006", "R8",
                            f"Subtarea '{sub_nom}' ya existe — nombre duplicado",
                            sent
                        )
                    self.tabla.agregar(
                        sub_nom, "TAREA", tipo="SUBTAREA",
                        grupo=nombre,
                        contexto=nombre,
                    )
                    nuevas_subs.append(sub_nom)

        self.tabla.actualizar(nombre, "subtareas", nuevas_subs,
                              "DIV.TAR — subtareas creadas")

    def _cre_subtarea(self, nodo):
        """
        CRE.SUBTAR
        R10 — se registra como subtarea (padre implícito).
        """
        nombre = self._valor_hijo(nodo, "NOMBRE_SUBTAREA")
        if not nombre:
            return
        sent = self._nombre_sentencia(nodo)

        if self.tabla.existe(nombre):
            raise ErrorSemantico(
                "E006", "R8",
                f"Subtarea '{nombre}' ya existe",
                sent
            )
        self.tabla.agregar(nombre, "TAREA", tipo="SUBTAREA")

    def _rec_tarea(self, nodo):
        """
        REC.TAR
        R8  — no duplicar.
        R15 — HASTA debe ser posterior a hoy.
        """
        nombre = self._valor_hijo(nodo, "NOMBRE_TAREA")
        if not nombre:
            return
        sent = self._nombre_sentencia(nodo)

        # R3 — sesión activa
        self._chk_sesion_activa(sent)

        # R8 — no duplicar
        if self.tabla.existe(nombre):
            e = self.tabla.obtener(nombre)
            raise ErrorSemantico(
                "E006", "R8",
                f"Tarea recurrente '{nombre}' ya declarada (línea {e['linea']})",
                sent
            )

        # Frecuencia
        frec = self._hijo(nodo, "FRECUENCIA")
        tipo_rec = "—"
        if frec and frec.hijos:
            for h in frec.hijos:
                if h.etiqueta not in ("CADA", "(", ")"):
                    tipo_rec = h.etiqueta

        # R15 — HASTA posterior a hoy
        limite = self._hijo(nodo, "LIMITE")
        fecha_str = "—"
        if limite:
            ef = self._hijo(limite, "EXPR_FECHA")
            if ef and ef.hijos:
                fecha_str = ef.hijos[0].etiqueta
                self._chk_fecha_valida(fecha_str, nombre, sent)

        self.tabla.agregar(
            nombre, "TAREA", tipo=f"RECURRENTE/{tipo_rec}",
            fecha_limite=fecha_str,
        )

    def _ver_avan(self, nodo):
        """VER.AVAN — R8: tarea debe existir."""
        nombre = self._valor_hijo(nodo, "NOMBRE_TAREA")
        self._chk_tarea_existe(nombre, self._nombre_sentencia(nodo))

    def _autoevaluar(self, nodo):
        """
        AUTO.EVAL
        R8  — tarea debe existir.
        R12 — el usuario activo debe ser el asignado.
        """
        nombre = self._valor_hijo(nodo, "NOMBRE_TAREA")
        sent   = self._nombre_sentencia(nodo)

        self._chk_tarea_existe(nombre, sent)

        entrada      = self.tabla.obtener(nombre)
        usuario_act  = self.tabla.usuario_activo()
        asignado     = entrada.get("asignado_a", "—")

        # R12
        if asignado != "—" and usuario_act and asignado != usuario_act:
            raise ErrorSemantico(
                "E010", "R12",
                f"AUTO.EVAL no permitida: la tarea '{nombre}' está asignada "
                f"a '{asignado}', no a '{usuario_act}'",
                sent
            )

    def _calificar(self, nodo):
        """
        CAL
        R8  — tarea debe existir.
        R13 — valor entre 0 y 100.
        """
        nombre = self._valor_hijo(nodo, "NOMBRE_TAREA")
        sent   = self._nombre_sentencia(nodo)

        self._chk_tarea_existe(nombre, sent)

        # Buscar el número de calificación en los hijos directos del nodo
        calificacion = None
        for h in nodo.hijos:
            if h.etiqueta.isdigit():
                calificacion = int(h.etiqueta)
                break
            # También puede estar como hoja directa numérica
            try:
                calificacion = int(h.etiqueta)
                break
            except (ValueError, AttributeError):
                pass

        # R13
        if calificacion is not None and not (0 <= calificacion <= 100):
            raise ErrorSemantico(
                "E011", "R13",
                f"Calificación {calificacion} fuera de rango — "
                f"debe estar entre 0 y 100",
                sent
            )

        if calificacion is not None:
            self.tabla.actualizar(nombre, "estado", f"CAL:{calificacion}",
                                  "calificación asignada")

    # ── Etiquetas y filtros ───────────────────────────────────

    def _etiquetar(self, nodo):
        """ETIQ.TAR — R8: tarea debe existir."""
        nombre = self._valor_hijo(nodo, "NOMBRE_TAREA")
        sent   = self._nombre_sentencia(nodo)
        self._chk_tarea_existe(nombre, sent)

        agregar = self._hijo(nodo, "AGREGAR")
        if agregar:
            etiquetas = [h.hijos[0].etiqueta.strip('"')
                         for h in agregar.hijos
                         if h.etiqueta == "ETIQUETA" and h.hijos]
            entrada = self.tabla.obtener(nombre)
            actuales = entrada.get("etiquetas", [])
            self.tabla.actualizar(nombre, "etiquetas",
                                  actuales + etiquetas, "ETIQ.TAR")

    def _filtro(self, nodo):
        """
        FILTRO.TAR
        R18 — vista no duplicada.
        R19 — condiciones válidas.
        """
        sent = self._nombre_sentencia(nodo)

        # R19 — validar condiciones
        cond_comb = self._hijo(nodo, "CONDICION_COMBINADA")
        if cond_comb:
            for c in cond_comb.hijos:
                if c.etiqueta == "CONDICION":
                    for hh in c.hijos:
                        if hh.etiqueta in self.PRIORIDADES_VALIDAS:
                            self.tabla.validar(hh.etiqueta,
                                               "prioridad válida ✓")
                        elif hh.etiqueta in self.ESTADOS_VALIDOS:
                            self.tabla.validar(hh.etiqueta,
                                               "estado válido ✓")
                        elif hh.etiqueta == "TAREA":
                            tar = self._valor_hijo(c, "TAREA")
                            if tar:
                                self._chk_tarea_existe(tar, sent)
                        elif hh.etiqueta not in (
                            "EST.TAR","(",")",",",";",
                            "ETIQ","ETIQUETA","==","!=",">","<",">=","<="
                        ):
                            # Si es un token libre que no reconocemos como válido
                            pass

        # Vista generada
        vista = self._hijo(nodo, "VISTA")
        if vista:
            nombre_vista = self._valor_hijo(vista, "NOMBRE_VISTA")
            if nombre_vista:
                # R18 — no duplicar vista
                if self.tabla.existe(nombre_vista):
                    raise ErrorSemantico(
                        "E015", "R18",
                        f"Vista '{nombre_vista}' ya existe — use un nombre distinto",
                        sent
                    )
                self.tabla.agregar(nombre_vista, "VISTA", tipo="VISTA/filtro")

    def _ver_vista(self, nodo):
        """VER.VISTA — vista debe existir (R18 inverso)."""
        nombre = self._valor_hijo(nodo, "NOMBRE_VISTA")
        sent   = self._nombre_sentencia(nodo)
        if nombre and not self.tabla.existe(nombre):
            raise ErrorSemantico(
                "E015", "R18",
                f"Vista '{nombre}' no existe — créela con FILTRO.TAR primero",
                sent
            )
        if nombre:
            self.tabla.validar(nombre, "vista existe ✓")

    # ── Notificaciones ────────────────────────────────────────

    def _notif_cuando(self, nodo):
        """
        NOTIF.CUANDO
        R20 — usuario destino debe existir.
        R8  — tarea en condición debe existir.
        """
        sent = self._nombre_sentencia(nodo)

        cond = self._hijo(nodo, "CONDICION_COMBINADA")
        if cond:
            for c in cond.hijos:
                if c.etiqueta == "CONDICION":
                    tarea_n = self._hijo(c, "TAREA")
                    if tarea_n and tarea_n.hijos:
                        nom = tarea_n.hijos[0].etiqueta
                        self._chk_tarea_existe(nom, sent)

        enviar = self._hijo(nodo, "ENVIAR")
        if enviar:
            usr = self._valor_hijo(enviar, "USUARIO")
            # R20
            self._chk_usuario_existe(usr, sent)

    def _notif_recordar(self, nodo):
        """NOTIF.RECORDAR — R20: usuario debe existir."""
        sent    = self._nombre_sentencia(nodo)
        usr_ref = self._hijo(nodo, "USUARIO_REF")
        if usr_ref:
            usr = self._valor_hijo(usr_ref, "USUARIO")
            self._chk_usuario_existe(usr, sent)

    def _suscribir(self, nodo):
        """
        SUSCRIBIR
        R20 — usuario debe existir.
        R21 — tarea debe existir.
        """
        sent = self._nombre_sentencia(nodo)
        usr  = self._valor_hijo(nodo, "USUARIO")
        # R20
        self._chk_usuario_existe(usr, sent)

        tar_ref = self._hijo(nodo, "TAREA_REF")
        if tar_ref:
            nom_tarea = self._valor_hijo(tar_ref, "NOMBRE_TAREA")
            # R21
            self._chk_tarea_existe(nom_tarea, sent)
            entrada = self.tabla.obtener(nom_tarea)
            subs    = entrada.get("suscriptores", [])
            if usr not in subs:
                self.tabla.actualizar(nom_tarea, "suscriptores",
                                      subs + [usr], "SUSCRIBIR")

    # ── Listas ───────────────────────────────────────────────

    def _cre_lista(self, nodo):
        """
        CRE.LIS
        R16 — no duplicar lista.
        """
        sent  = self._nombre_sentencia(nodo)
        titulo = None
        tit_n  = self._hijo(nodo, "TITULO_LISTA")
        if tit_n:
            t = self._hijo(tit_n, "TEXTO")
            if t and t.hijos:
                titulo = t.hijos[0].etiqueta.strip('"')

        nombre = titulo or f"lista_{len(self.tabla.por_categoria('LISTA'))+1}"

        # R16
        if self.tabla.existe(nombre):
            raise ErrorSemantico(
                "E013", "R16",
                f"Lista '{nombre}' ya fue declarada — no puede crearse dos veces",
                sent
            )

        desc = None
        desc_n = self._hijo(nodo, "DESC_LISTA")
        if desc_n:
            d = self._hijo(desc_n, "TEXTO")
            if d and d.hijos:
                desc = d.hijos[0].etiqueta.strip('"')

        self.tabla.agregar(
            nombre, "LISTA", tipo="LISTA",
            descripcion=desc or "—",
        )

    def _ag_lista(self, nodo):
        """
        AG.LIS
        R17 — lista debe existir.
        R8  — tarea debe existir.
        """
        sent        = self._nombre_sentencia(nodo)
        nombre_list = self._valor_hijo(nodo, "NOMBRE_LISTA")

        # R17
        self._chk_lista_existe(nombre_list, sent)

        en_lis = self._hijo(nodo, "EN_LISTA")
        if en_lis:
            tarea = self._valor_hijo(en_lis, "NOMBRE_LISTA")
            self._chk_tarea_existe(tarea, sent)
            entrada = self.tabla.obtener(nombre_list)
            tl      = entrada.get("tareas_lista", [])
            if tarea not in tl:
                self.tabla.actualizar(nombre_list, "tareas_lista",
                                      tl + [tarea], "AG.LIS")

    def _ver_lista(self, nodo):
        nombre = self._valor_hijo(nodo, "NOMBRE_LISTA")
        self._chk_lista_existe(nombre, self._nombre_sentencia(nodo))

    def _elim_lista(self, nodo):
        nombre = self._valor_hijo(nodo, "NOMBRE_LISTA")
        self._chk_lista_existe(nombre, self._nombre_sentencia(nodo))

    # ── Comentarios ───────────────────────────────────────────

    def _comentario(self, nodo):
        nombre = self._valor_hijo(nodo, "NOMBRE_TAREA")
        self._chk_tarea_existe(nombre, self._nombre_sentencia(nodo))

    # ── Mensajes ─────────────────────────────────────────────

    def _env_msg(self, nodo):
        dest = self._valor_hijo(nodo, "DESTINATARIO")
        self._chk_usuario_existe(dest, self._nombre_sentencia(nodo))

    def _env_enl(self, nodo):
        dest = self._valor_hijo(nodo, "DESTINATARIO")
        self._chk_usuario_existe(dest, self._nombre_sentencia(nodo))

    # ── Modularidad ───────────────────────────────────────────

    def _importar(self, nodo):
        archivo = self._valor_hijo(nodo, "ARCHIVO")
        nombre  = archivo or "modulo_importado"
        if not self.tabla.existe(nombre):
            self.tabla.agregar(nombre, "MODULO", tipo="IMPORT")

    def _exportar(self, nodo):
        """EXPORTAR.TAR — R8: tarea debe existir."""
        nombre = self._valor_hijo(nodo, "NOMBRE_TAREA")
        sent   = self._nombre_sentencia(nodo)
        self._chk_tarea_existe(nombre, sent)

        destino = self._hijo(nodo, "DESTINO")
        if destino:
            arch = self._valor_hijo(destino, "ARCHIVO")
            self.tabla.actualizar(nombre, "descripcion",
                                  f"exportada → {arch}", "EXPORTAR.TAR")

    def _usar_bib(self, nodo):
        nombre = self._valor_hijo(nodo, "BIBLIOTECA")
        if nombre and not self.tabla.existe(nombre):
            self.tabla.agregar(nombre, "BIBLIOTECA", tipo="BIB")

    # ═══════════════════════════════════════════════════════════
    # PASO 5: FINALIZACIÓN
    # ═══════════════════════════════════════════════════════════

    def _imprimir_ok(self):
        print("\n✅ ANÁLISIS SEMÁNTICO CORRECTO\n")
        self.tabla.imprimir()
        print("\n📋 LOG DE CONSTRUCCIÓN DE LA TABLA (paso a paso):")
        print("─" * 70)
        for e in self.tabla.log():
            l = f"  (L{e['linea']})" if e['linea'] else ""
            print(f"  Paso {e['paso']:02d} [{e['accion']:<10}]{l:<8}  {e['detalle']}")
        print("─" * 70)


# ─────────────────────────────────────────────────────────────
# MAIN — prueba en consola
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sem = AnalizadorSemantico()
    print("Ingrese el código (línea vacía para terminar):\n")
    entrada = ""
    while True:
        linea = input()
        if linea == "":
            break
        entrada += linea + "\n"

    tabla, log, ok, msg, detalle = sem.analizar(entrada)
    if not ok:
        print(f"\n❌ {msg}")
        if detalle:
            print(f"   {detalle}")
