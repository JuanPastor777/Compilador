"""
Analizador Sintáctico — Lenguaje de Gestión de Proyectos
Descendente recursivo con construcción de árbol sintáctico.
"""

from Lexico import AnalizadorLexico




class Nodo:
    def __init__(self, etiqueta, valor=None):
        self.etiqueta = etiqueta   # Nombre del nodo ( PROGRAMA, SENTENCIA, FEC…)
        self.valor = valor         # Lexema literal si es hoja ("juan", "2026-12-31")
        self.hijos = []

    def agregar(self, hijo):
        self.hijos.append(hijo)
        return hijo

    def hoja(self, lexema):

        n = Nodo(lexema)
        self.hijos.append(n)
        return n

    def a_dict(self):

        d = {"nombre": self.etiqueta, "hijos": [h.a_dict() for h in self.hijos]}
        return d

    def imprimir(self, prefijo="", es_ultimo=True):

        conector = "└── " if es_ultimo else "├── "
        print(prefijo + conector + self.etiqueta)
        extension = "    " if es_ultimo else "│   "
        for i, hijo in enumerate(self.hijos):
            hijo.imprimir(prefijo + extension, i == len(self.hijos) - 1)

    def a_texto(self, prefijo="", es_ultimo=True):

        conector = "└── " if es_ultimo else "├── "
        linea = prefijo + conector + self.etiqueta + "\n"
        extension = "    " if es_ultimo else "│   "
        for i, hijo in enumerate(self.hijos):
            linea += hijo.a_texto(prefijo + extension, i == len(self.hijos) - 1)
        return linea



class ErrorSintactico(Exception):
    def __init__(self, mensaje, linea=0):
        super().__init__(mensaje)
        self.linea = linea
        self.mensaje = f"Línea {linea}: {mensaje}" if linea else mensaje


# ─────────────────────────────────────────────────────────────
# ANALIZADOR SINTÁCTICO
# ─────────────────────────────────────────────────────────────

class AnalizadorSintactico:

    def __init__(self):
        self.lexico = AnalizadorLexico()
        self.tokens = []
        self.pos = 0

    # ── Utilidades de navegación ──────────────────────────────

    def token_actual(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return ("EOF", "EOF")

    def lexema(self):
        return self.token_actual()[0]

    def tipo(self):
        return self.token_actual()[1]

    def avanzar(self):
        tok = self.token_actual()
        self.pos += 1
        return tok

    def consumir(self, lexema_esperado=None, tipo_esperado=None):
        ##Consume el token actual si coincide; lanza error si no
        lex, tip = self.token_actual()
        linea = self.linea_actual()
        if lexema_esperado and lex != lexema_esperado:
            raise ErrorSintactico(
                f"Se esperaba '{lexema_esperado}' pero se encontró '{lex}'", linea
            )
        if tipo_esperado and tip != tipo_esperado:
            raise ErrorSintactico(
                f"Se esperaba tipo {tipo_esperado} pero se encontró '{lex}' ({tip})", linea
            )
        self.pos += 1
        return lex

    def es_fin(self):
        return self.pos >= len(self.tokens)

    def linea_actual(self):
        if hasattr(self, 'lineas') and self.pos < len(self.lineas):
            return self.lineas[self.pos]
        return 0

    # ── Punto de entrada ──────────────────────────────────────

    def analizar(self, texto):

        ##Analiza el texto fuente y devuelve (arbol, texto_arbol, exito, mensaje).

        tokens_raw = self.lexico.analizar(texto)
        self.tokens = tokens_raw
        # Asignar número de línea a cada token
        self.lineas = []
        for n_linea, linea in enumerate(texto.splitlines(), 1):
            toks_linea = self.lexico.analizar(linea)
            for _ in toks_linea:
                self.lineas.append(n_linea)
        # Si el conteo no coincide, rellenar con 0
        while len(self.lineas) < len(self.tokens):
            self.lineas.append(0)
        # Filtrar errores léxicos antes de comenzar
        errores_lexicos = [(lex, tip) for lex, tip in self.tokens
                           if tip in ("ERROR_LEXICO", "ERR_INV_DATE", "ERR_INV_TIME")]
        if errores_lexicos:
            msgs = [f"Error léxico: '{lex}' ({tip})" for lex, tip in errores_lexicos]
            return None, "", False, "\n".join(msgs)

        self.pos = 0
        try:
            arbol = self.programa()
            if not self.es_fin():
                lex, tip = self.token_actual()
                raise ErrorSintactico(f"Token inesperado al final: '{lex}'", self.linea_actual())
            texto_arbol = "PROGRAMA\n" + "".join(
                hijo.a_texto("", i == len(arbol.hijos) - 1)
                for i, hijo in enumerate(arbol.hijos)
            )
            print("\n Cadena aceptada\n")
            print("Árbol sintáctico:\n")
            print("PROGRAMA")
            for i, hijo in enumerate(arbol.hijos):
                hijo.imprimir("", i == len(arbol.hijos) - 1)
            return arbol, texto_arbol, True, "Cadena aceptada"
        except ErrorSintactico as e:
            print(f"\n {e.mensaje}\n")
            return None, "", False, e.mensaje

    # ═══════════════════════════════════════════════════════════
    # GRAMÁTICA — REGLAS DE PRODUCCIÓN
    # ═══════════════════════════════════════════════════════════
    #
    # programa       → sentencia*
    # sentencia      → sent_usuario | sent_grupo | sent_tarea |
    #                  sent_recurrente | sent_etiqueta | sent_filtro |
    #                  sent_vista | sent_notif | sent_lista |
    #                  sent_comentario | sent_mensaje | sent_importar |
    #                  sent_exportar | sent_biblioteca |
    #                  sent_autoevaluar | sent_calificar | sent_ver
    # modificadores  → modificador*
    # modificador    → mod_descripcion | mod_fecha | mod_prioridad |
    #                  mod_estado | mod_en_lista | mod_asig_usr
    # expr_fecha     → FECHA | EXPR_FECHA | HORA | fecha_relativa
    # fecha_relativa → HOY + NUMERO UNIDAD | keyword_fecha
    # condicion      → EST.TAR ( TEXTO ) OP_CMP estado_token
    #                | prioridad_token | estado_token
    # condicion_comb → condicion ( OP_LOG condicion )*
    #
    # ═══════════════════════════════════════════════════════════

    def programa(self):
        nodo = Nodo("PROGRAMA")
        while not self.es_fin():
            nodo.agregar(self.sentencia())
        return nodo



    DISPATCH = {
        # Usuarios
        "REG.USR":      "sent_reg_usr",
        "ING.USR":      "sent_ing_usr",
        "CRE.USR":      "sent_cre_usr",
        "BUS.USR":      "sent_bus_usr",
        "SALIR":        "sent_simple",
        "MENU":         "sent_simple",
        # Grupos
        "CRE.GRP":      "sent_cre_grp",
        "ASIG.USR":     "sent_asig_usr",
        # Tareas
        "CRE.TAR":      "sent_cre_tar",
        "CRE.TAR.IND":  "sent_cre_tar",
        "CRE.TAR.GRP":  "sent_cre_tar",
        "VER.TAR.IND":  "sent_ver_tar_ind",
        "ASIG.TAR":     "sent_asig_tar",
        "VER.AVAN":     "sent_ver_avan",
        "CRE.SUBTAR":   "sent_cre_subtar",
        "DIV.TAR":      "sent_div_tar",
        # Evaluación
        "AUTO.EVAL":    "sent_autoevaluar",
        "CAL":          "sent_calificar",
        # Recurrente
        "REC.TAR":      "sent_recurrente",
        # Etiquetas / filtros / vistas
        "ETIQ.TAR":     "sent_etiqueta",
        "FILTRO.TAR":   "sent_filtro",
        "VER.VISTA":    "sent_ver_vista",
        # Notificaciones
        "NOTIF.CUANDO": "sent_notif_cuando",
        "NOTIF.RECORDAR":"sent_notif_recordar",
        "SUSCRIBIR":    "sent_suscribir",
        # Listas
        "CRE.LIS":      "sent_cre_lis",
        "VER.LIS":      "sent_ver_lis",
        "AG.LIS":       "sent_ag_lis",
        "ELIM.LIS":     "sent_elim_lis",
        # Comentarios
        "COM":          "sent_comentario",
        "COM.MEJ":      "sent_comentario",
        "COM.AVAN":     "sent_comentario",
        "COM.ASIG":     "sent_comentario",
        # Mensajes
        "ENV.MSG":      "sent_env_msg",
        "ENV.ENL":      "sent_env_enl",
        "VER.MSG":      "sent_ver_msg",
        # Modularidad
        "IMPORT":       "sent_import",
        "EXPORTAR.TAR": "sent_exportar",
        "USAR.BIB":     "sent_usar_bib",
    }

    def sentencia(self):
        lex = self.lexema()
        metodo = self.DISPATCH.get(lex)
        if metodo:
            return getattr(self, metodo)()
        raise ErrorSintactico(
            f"Instrucción no reconocida: '{lex}'"
        , self.linea_actual())



    def abrir(self, nodo):
        nodo.hoja(self.consumir("("))

    def cerrar(self, nodo):
        nodo.hoja(self.consumir(")"))

    def punto_coma(self, nodo):
        nodo.hoja(self.consumir(";"))

    def coma(self, nodo):
        nodo.hoja(self.consumir(","))

    def arg_texto_o_cadena(self, nodo_padre, etiqueta="ARG"):
        """Acumula todos los tokens hasta ) o , como un argumento."""
        STOP = {")", ",", ";", "EOF"}
        linea = self.linea_actual()

        if self.lexema() in STOP:
            raise ErrorSintactico(
                f"Se esperaba un argumento pero se encontró '{self.lexema()}'", linea
            )

        partes = []
        while not self.es_fin() and self.lexema() not in STOP:
            partes.append(self.avanzar()[0])

        n = Nodo(etiqueta)
        n.hoja(" ".join(partes))
        nodo_padre.agregar(n)
        return n
    def bloque_par(self, nodo_padre, etiqueta, fn_interior):
        """Genera:  etiqueta ( <fn_interior> )  como hijo del nodo_padre."""
        n = Nodo(etiqueta)
        nodo_padre.agregar(n)
        self.abrir(n)
        fn_interior(n)
        self.cerrar(n)
        return n



    MODIFICADORES_PRIORIDAD = {"PRI.URG", "PRI.ALT", "PRI.MED", "PRI.BAJ"}
    MODIFICADORES_ESTADO    = {"EST.PEN", "EST.ACT", "EST.REV",
                               "EST.COR", "EST.APROB", "EST.RECH", "EST.FIN"}
    KEYWORDS_FECHA          = {"HOY", "FIN.MES", "FIN.SEM", "INI.MES", "INI.SEM",
                               "PROX.LUN", "PROX.MAR", "PROX.MIE", "PROX.JUE",
                               "PROX.VIE", "PROX.SAB", "PROX.DOM"}
    UNIDADES_TIEMPO         = {"DIA", "DIAS", "SEMANA", "SEMANAS", "MES", "MESES", "ANNO"}

    def modificadores(self, nodo):

        while not self.es_fin() and self.lexema() != ";":
            lex = self.lexema()
            if lex == "DES":
                self.mod_descripcion(nodo)
            elif lex == "FEC":
                self.mod_fecha(nodo)
            elif lex in self.MODIFICADORES_PRIORIDAD:
                m = Nodo("PRIORIDAD")
                nodo.agregar(m)
                m.hoja(self.avanzar()[0])
            elif lex in self.MODIFICADORES_ESTADO:
                m = Nodo("ESTADO")
                nodo.agregar(m)
                m.hoja(self.avanzar()[0])
            elif lex == "EN.LIS":
                self.mod_en_lis(nodo)
            elif lex == "ASIG.USR":
                self.mod_asig_usr(nodo)
            elif lex == "LIS.TIT":
                self.mod_lis_tit(nodo)
            elif lex == "LIS.DESC":
                self.mod_lis_desc(nodo)
            else:
                break

    def mod_descripcion(self, nodo):
        m = Nodo("DESCRIPCION")
        nodo.agregar(m)
        m.hoja(self.consumir("DES"))
        self.abrir(m)
        self.arg_texto_o_cadena(m, "TEXTO")
        self.cerrar(m)

    def mod_fecha(self, nodo):
        m = Nodo("FECHA_MOD")
        nodo.agregar(m)
        m.hoja(self.consumir("FEC"))
        self.abrir(m)
        self.expr_fecha(m)
        self.cerrar(m)

    def mod_en_lis(self, nodo):
        m = Nodo("EN_LISTA")
        nodo.agregar(m)
        m.hoja(self.consumir("EN.LIS"))
        self.abrir(m)
        self.arg_texto_o_cadena(m, "NOMBRE_LISTA")
        self.cerrar(m)

    def mod_asig_usr(self, nodo):
        m = Nodo("ASIG_USUARIO")
        nodo.agregar(m)
        m.hoja(self.consumir("ASIG.USR"))
        self.abrir(m)
        self.arg_texto_o_cadena(m, "USUARIO")
        self.cerrar(m)

    def mod_lis_tit(self, nodo):
        m = Nodo("TITULO_LISTA")
        nodo.agregar(m)
        m.hoja(self.consumir("LIS.TIT"))
        self.abrir(m)
        self.arg_texto_o_cadena(m, "TEXTO")
        self.cerrar(m)

    def mod_lis_desc(self, nodo):
        m = Nodo("DESC_LISTA")
        nodo.agregar(m)
        m.hoja(self.consumir("LIS.DESC"))
        self.abrir(m)
        self.arg_texto_o_cadena(m, "TEXTO")
        self.cerrar(m)

    # ── Expresiones de fecha ──────────────────────────────────

    def expr_fecha(self, nodo):
        """
        expr_fecha → FECHA | EXPR_FECHA | HORA | keyword_fecha
                   | HOY + NUMERO UNIDAD
        """
        tip = self.tipo()
        lex = self.lexema()
        ef = Nodo("EXPR_FECHA")
        nodo.agregar(ef)

        if tip in ("FECHA", "EXPR_FECHA", "HORA"):
            ef.hoja(self.avanzar()[0])
        elif lex == "HOY":
            ef.hoja(self.avanzar()[0])          # HOY
            if self.lexema() in ("+", "-"):
                ef.hoja(self.avanzar()[0])      # + ó -
                if self.tipo() != "NUMERO":
                    raise ErrorSintactico("Se esperaba un número después de HOY +/-", self.linea_actual())
                ef.hoja(self.avanzar()[0])      # N
                if self.lexema() not in self.UNIDADES_TIEMPO:
                    raise ErrorSintactico(
                        f"Se esperaba unidad de tiempo (DIA, SEMANA…) pero se encontró '{self.lexema()}'"
                    , self.linea_actual())
                ef.hoja(self.avanzar()[0])      # DIAS / SEMANAS / …
        elif lex in self.KEYWORDS_FECHA:
            ef.hoja(self.avanzar()[0])
        else:
            raise ErrorSintactico(
                f"Se esperaba una expresión de fecha pero se encontró '{lex}'"
            , self.linea_actual())
        return ef

    # ── Condiciones para FILTRO / NOTIF ───────────────────────

    def condicion_simple(self, nodo):
        """
        condicion_simple → EST.TAR ( TEXTO ) OP_CMP ESTADO
                         | prioridad | estado
        """
        c = Nodo("CONDICION")
        nodo.agregar(c)
        lex = self.lexema()

        if lex == "EST.TAR":
            c.hoja(self.avanzar()[0])           # EST.TAR
            self.abrir(c)
            self.arg_texto_o_cadena(c, "TAREA")
            self.cerrar(c)
            if self.tipo() != "OPERADOR_COMPARACION":
                raise ErrorSintactico(
                    f"Se esperaba operador de comparación pero se encontró '{self.lexema()}'"
                , self.linea_actual())
            c.hoja(self.avanzar()[0])           # == / != / …
            if self.lexema() not in self.MODIFICADORES_ESTADO:
                raise ErrorSintactico(
                    f"Se esperaba un estado (EST.PEN, EST.ACT…) pero se encontró '{self.lexema()}'"
                , self.linea_actual())
            c.hoja(self.avanzar()[0])           # EST.xxx
        elif lex in self.MODIFICADORES_PRIORIDAD:
            c.hoja(self.avanzar()[0])
        elif lex in self.MODIFICADORES_ESTADO:
            c.hoja(self.avanzar()[0])
        elif lex == "ETIQ":
            c.hoja(self.avanzar()[0])           # ETIQ
            self.abrir(c)
            self.arg_texto_o_cadena(c, "ETIQUETA")
            self.cerrar(c)
        else:
            raise ErrorSintactico(
                f"Se esperaba una condición válida pero se encontró '{lex}'"
            , self.linea_actual())
        return c

    def condicion_combinada(self, nodo):
        """condicion ( (Y|O|NO) condicion )*"""
        cc = Nodo("CONDICION_COMBINADA")
        nodo.agregar(cc)
        self.condicion_simple(cc)
        while self.tipo() == "OPERADOR_LOGICO":
            cc.hoja(self.avanzar()[0])          # Y / O / NO
            self.condicion_simple(cc)
        return cc

    # ═══════════════════════════════════════════════════════════
    # SENTENCIAS INDIVIDUALES
    # ═══════════════════════════════════════════════════════════

    # ── Usuarios ──────────────────────────────────────────────

    def sent_reg_usr(self):
        # REG.USR ( TEXTO , CADENA , ROL ) ;
        s = Nodo("SENT_REG_USUARIO")
        s.hoja(self.consumir("REG.USR"))
        self.abrir(s)
        self.arg_texto_o_cadena(s, "USUARIO")
        if self.lexema() == ",":
            self.coma(s)
            self.arg_texto_o_cadena(s, "NOMBRE_COMPLETO")
        if self.lexema() == ",":
            self.coma(s)
            rol = self.lexema()
            if rol not in ("ROL.COORD", "ROL.MIEM"):
                raise ErrorSintactico(f"Se esperaba ROL.COORD o ROL.MIEM pero se encontró '{rol}'", self.linea_actual())
            s.hoja(self.avanzar()[0])
        self.cerrar(s)
        self.punto_coma(s)
        return s

    def sent_ing_usr(self):
        # ING.USR ( TEXTO ) ;
        s = Nodo("SENT_INGRESO_USUARIO")
        s.hoja(self.consumir("ING.USR"))
        self.abrir(s)
        self.arg_texto_o_cadena(s, "USUARIO")
        self.cerrar(s)
        self.punto_coma(s)
        return s

    def sent_cre_usr(self):
        s = Nodo("SENT_CREAR_USUARIO")
        s.hoja(self.consumir("CRE.USR"))
        self.abrir(s)
        self.arg_texto_o_cadena(s, "USUARIO")
        self.cerrar(s)
        self.modificadores(s)
        self.punto_coma(s)
        return s

    def sent_bus_usr(self):
        s = Nodo("SENT_BUSCAR_USUARIO")
        s.hoja(self.consumir("BUS.USR"))
        self.abrir(s)
        self.arg_texto_o_cadena(s, "CRITERIO")
        self.cerrar(s)
        self.punto_coma(s)
        return s

    def sent_simple(self):
        # SALIR ; | MENU ;
        s = Nodo(f"SENT_{self.lexema()}")
        s.hoja(self.avanzar()[0])
        self.punto_coma(s)
        return s

    # ── Grupos ────────────────────────────────────────────────

    def sent_cre_grp(self):
        # CRE.GRP ( TEXTO ) [ASIG.USR(…)]* ;
        s = Nodo("SENT_CREAR_GRUPO")
        s.hoja(self.consumir("CRE.GRP"))
        self.abrir(s)
        self.arg_texto_o_cadena(s, "NOMBRE_GRUPO")
        self.cerrar(s)
        self.modificadores(s)
        self.punto_coma(s)
        return s

    def sent_asig_usr(self):
        # ASIG.USR ( TEXTO ) ;
        s = Nodo("SENT_ASIGNAR_USUARIO")
        s.hoja(self.consumir("ASIG.USR"))
        self.abrir(s)
        self.arg_texto_o_cadena(s, "USUARIO")
        self.cerrar(s)
        self.punto_coma(s)
        return s

    # ── Tareas ────────────────────────────────────────────────

    def sent_cre_tar(self):
        # CRE.TAR[.IND|.GRP] ( TEXTO ) modificadores ;
        cmd = self.lexema()
        s = Nodo("SENT_CREAR_TAREA")
        s.hoja(self.avanzar()[0])
        self.abrir(s)
        self.arg_texto_o_cadena(s, "NOMBRE_TAREA")
        self.cerrar(s)
        self.modificadores(s)
        self.punto_coma(s)
        return s

    def sent_ver_tar_ind(self):
        s = Nodo("SENT_VER_TAREAS_IND")
        s.hoja(self.consumir("VER.TAR.IND"))
        self.punto_coma(s)
        return s

    def sent_asig_tar(self):
        # ASIG.TAR ( TEXTO ) ASIG.USR ( TEXTO ) ;
        s = Nodo("SENT_ASIGNAR_TAREA")
        s.hoja(self.consumir("ASIG.TAR"))
        self.abrir(s)
        self.arg_texto_o_cadena(s, "NOMBRE_TAREA")
        self.cerrar(s)
        self.modificadores(s)
        self.punto_coma(s)
        return s

    def sent_ver_avan(self):
        s = Nodo("SENT_VER_AVANCE")
        s.hoja(self.consumir("VER.AVAN"))
        self.abrir(s)
        self.arg_texto_o_cadena(s, "NOMBRE_TAREA")
        self.cerrar(s)
        self.punto_coma(s)
        return s

    def sent_cre_subtar(self):
        # CRE.SUBTAR ( TEXTO ) EN.LIS? ;
        s = Nodo("SENT_CREAR_SUBTAREA")
        s.hoja(self.consumir("CRE.SUBTAR"))
        self.abrir(s)
        self.arg_texto_o_cadena(s, "NOMBRE_SUBTAREA")
        self.cerrar(s)
        self.modificadores(s)
        self.punto_coma(s)
        return s

    def sent_div_tar(self):
        # DIV.TAR ( TEXTO ) CRE.SUBTAR ( TEXTO ) [CRE.SUBTAR ( TEXTO )]* ;
        s = Nodo("SENT_DIVIDIR_TAREA")
        s.hoja(self.consumir("DIV.TAR"))
        self.abrir(s)
        self.arg_texto_o_cadena(s, "NOMBRE_TAREA")
        self.cerrar(s)
        while self.lexema() == "CRE.SUBTAR":
            sub = Nodo("SUBTAREA")
            s.agregar(sub)
            sub.hoja(self.consumir("CRE.SUBTAR"))
            self.abrir(sub)
            self.arg_texto_o_cadena(sub, "NOMBRE")
            self.cerrar(sub)
        self.punto_coma(s)
        return s

    def sent_autoevaluar(self):
        s = Nodo("SENT_AUTOEVALUAR")
        s.hoja(self.consumir("AUTO.EVAL"))
        self.abrir(s)
        self.arg_texto_o_cadena(s, "NOMBRE_TAREA")
        self.cerrar(s)
        self.punto_coma(s)
        return s

    def sent_calificar(self):
        # CAL ( TEXTO , NUMERO ) ;
        s = Nodo("SENT_CALIFICAR")
        s.hoja(self.consumir("CAL"))
        self.abrir(s)
        self.arg_texto_o_cadena(s, "NOMBRE_TAREA")
        self.coma(s)
        if self.tipo() != "NUMERO":
            raise ErrorSintactico(f"Se esperaba una calificación numérica pero se encontró '{self.lexema()}'", self.linea_actual())
        s.hoja(self.avanzar()[0])
        self.cerrar(s)
        self.punto_coma(s)
        return s

    # ── Recurrentes ───────────────────────────────────────────

    def sent_recurrente(self):
        # REC.TAR ( TEXTO ) CADA ( UNIDAD ) [HASTA ( expr_fecha )] [A ( HORA )] ;
        s = Nodo("SENT_TAREA_RECURRENTE")
        s.hoja(self.consumir("REC.TAR"))
        self.abrir(s)
        self.arg_texto_o_cadena(s, "NOMBRE_TAREA")
        self.cerrar(s)

        if self.lexema() != "CADA":
            raise ErrorSintactico(f"Se esperaba CADA después de REC.TAR(...) pero se encontró '{self.lexema()}'", self.linea_actual())
        c = Nodo("FRECUENCIA")
        s.agregar(c)
        c.hoja(self.consumir("CADA"))
        self.abrir(c)
        if self.lexema() not in self.UNIDADES_TIEMPO:
            raise ErrorSintactico(f"Se esperaba unidad de tiempo (DIA, SEMANA, MES…) pero se encontró '{self.lexema()}'", self.linea_actual())
        c.hoja(self.avanzar()[0])
        self.cerrar(c)

        if self.lexema() == "HASTA":
            h = Nodo("LIMITE")
            s.agregar(h)
            h.hoja(self.consumir("HASTA"))
            self.abrir(h)
            self.expr_fecha(h)
            self.cerrar(h)

        if self.lexema() == "A":
            hora_n = Nodo("HORA_EJECUCION")
            s.agregar(hora_n)
            hora_n.hoja(self.consumir("A"))
            self.abrir(hora_n)
            if self.tipo() != "HORA":
                raise ErrorSintactico(f"Se esperaba una hora (HH:MM) pero se encontró '{self.lexema()}'", self.linea_actual())
            hora_n.hoja(self.avanzar()[0])
            self.cerrar(hora_n)

        self.punto_coma(s)
        return s

    # ── Etiquetas, filtros y vistas ───────────────────────────

    def sent_etiqueta(self):
        # ETIQ.TAR ( TEXTO ) AGREGAR ( CADENA [, CADENA]* ) ;
        s = Nodo("SENT_ETIQUETAR")
        s.hoja(self.consumir("ETIQ.TAR"))
        self.abrir(s)
        self.arg_texto_o_cadena(s, "NOMBRE_TAREA")
        self.cerrar(s)

        if self.lexema() != "AGREGAR":
            raise ErrorSintactico(f"Se esperaba AGREGAR pero se encontró '{self.lexema()}'", self.linea_actual())
        a = Nodo("AGREGAR")
        s.agregar(a)
        a.hoja(self.consumir("AGREGAR"))
        self.abrir(a)
        self.arg_texto_o_cadena(a, "ETIQUETA")
        while self.lexema() == ",":
            self.coma(a)
            self.arg_texto_o_cadena(a, "ETIQUETA")
        self.cerrar(a)
        self.punto_coma(s)
        return s

    def sent_filtro(self):
        # FILTRO.TAR ( condicion_combinada ) VISTA ( CADENA ) ;
        s = Nodo("SENT_FILTRO")
        s.hoja(self.consumir("FILTRO.TAR"))
        self.abrir(s)
        self.condicion_combinada(s)
        self.cerrar(s)

        if self.lexema() != "VISTA":
            raise ErrorSintactico(f"Se esperaba VISTA después del filtro pero se encontró '{self.lexema()}'", self.linea_actual())
        v = Nodo("VISTA")
        s.agregar(v)
        v.hoja(self.consumir("VISTA"))
        self.abrir(v)
        self.arg_texto_o_cadena(v, "NOMBRE_VISTA")
        self.cerrar(v)
        self.punto_coma(s)
        return s

    def sent_ver_vista(self):
        # VER.VISTA ( CADENA ) ;
        s = Nodo("SENT_VER_VISTA")
        s.hoja(self.consumir("VER.VISTA"))
        self.abrir(s)
        self.arg_texto_o_cadena(s, "NOMBRE_VISTA")
        self.cerrar(s)
        self.punto_coma(s)
        return s

    # ── Notificaciones ────────────────────────────────────────

    def sent_notif_cuando(self):
        # NOTIF.CUANDO ( condicion ) ENVIAR ( TEXTO ) ;
        s = Nodo("SENT_NOTIF_CUANDO")
        s.hoja(self.consumir("NOTIF.CUANDO"))
        self.abrir(s)
        self.condicion_combinada(s)
        self.cerrar(s)

        if self.lexema() != "ENVIAR":
            raise ErrorSintactico(f"Se esperaba ENVIAR pero se encontró '{self.lexema()}'", self.linea_actual())
        e = Nodo("ENVIAR")
        s.agregar(e)
        e.hoja(self.consumir("ENVIAR"))
        self.abrir(e)
        self.arg_texto_o_cadena(e, "USUARIO")
        self.cerrar(e)
        self.punto_coma(s)
        return s

    def sent_notif_recordar(self):
        # NOTIF.RECORDAR ( USR ( TEXTO ) , FEC ( expr_fecha ) , CADENA ) ;
        s = Nodo("SENT_NOTIF_RECORDAR")
        s.hoja(self.consumir("NOTIF.RECORDAR"))
        self.abrir(s)

        usr = Nodo("USUARIO_REF")
        s.agregar(usr)
        usr.hoja(self.consumir("USR"))
        self.abrir(usr)
        self.arg_texto_o_cadena(usr, "USUARIO")
        self.cerrar(usr)

        self.coma(s)

        fec = Nodo("FECHA_REF")
        s.agregar(fec)
        fec.hoja(self.consumir("FEC"))
        self.abrir(fec)
        self.expr_fecha(fec)
        self.cerrar(fec)

        self.coma(s)
        self.arg_texto_o_cadena(s, "MENSAJE")

        self.cerrar(s)
        self.punto_coma(s)
        return s

    def sent_suscribir(self):
        # SUSCRIBIR ( TEXTO , TAR ( CADENA ) ) ;
        s = Nodo("SENT_SUSCRIBIR")
        s.hoja(self.consumir("SUSCRIBIR"))
        self.abrir(s)
        self.arg_texto_o_cadena(s, "USUARIO")
        self.coma(s)

        tar = Nodo("TAREA_REF")
        s.agregar(tar)
        tar.hoja(self.consumir("TAR"))
        self.abrir(tar)
        self.arg_texto_o_cadena(tar, "NOMBRE_TAREA")
        self.cerrar(tar)

        self.cerrar(s)
        self.punto_coma(s)
        return s

    # ── Listas ────────────────────────────────────────────────

    def sent_cre_lis(self):
        # CRE.LIS [LIS.TIT(…)] [LIS.DESC(…)] ;
        s = Nodo("SENT_CREAR_LISTA")
        s.hoja(self.consumir("CRE.LIS"))
        self.modificadores(s)
        self.punto_coma(s)
        return s

    def sent_ver_lis(self):
        s = Nodo("SENT_VER_LISTA")
        s.hoja(self.consumir("VER.LIS"))
        self.abrir(s)
        self.arg_texto_o_cadena(s, "NOMBRE_LISTA")
        self.cerrar(s)
        self.punto_coma(s)
        return s

    def sent_ag_lis(self):
        # AG.LIS ( CADENA ) EN.LIS ( TEXTO ) ;
        s = Nodo("SENT_AGREGAR_LISTA")
        s.hoja(self.consumir("AG.LIS"))
        self.abrir(s)
        self.arg_texto_o_cadena(s, "NOMBRE_LISTA")
        self.cerrar(s)
        self.modificadores(s)
        self.punto_coma(s)
        return s

    def sent_elim_lis(self):
        s = Nodo("SENT_ELIMINAR_LISTA")
        s.hoja(self.consumir("ELIM.LIS"))
        self.abrir(s)
        self.arg_texto_o_cadena(s, "NOMBRE_LISTA")
        self.cerrar(s)
        self.punto_coma(s)
        return s

    # ── Comentarios ───────────────────────────────────────────

    def sent_comentario(self):
        # COM[.MEJ|.AVAN|.ASIG] ( TEXTO ) COM.xxx ( CADENA ) ;
        cmd = self.lexema()
        s = Nodo("SENT_COMENTARIO")
        s.hoja(self.avanzar()[0])
        self.abrir(s)
        self.arg_texto_o_cadena(s, "NOMBRE_TAREA")
        self.cerrar(s)
        # Subtipo de comentario opcional
        sub = self.lexema()
        if sub in ("COM.MEJ", "COM.AVAN", "COM.ASIG"):
            c = Nodo("CONTENIDO_COMENTARIO")
            s.agregar(c)
            c.hoja(self.avanzar()[0])
            self.abrir(c)
            self.arg_texto_o_cadena(c, "TEXTO")
            self.cerrar(c)
        self.punto_coma(s)
        return s

    # ── Mensajes ──────────────────────────────────────────────

    def sent_env_msg(self):
        # ENV.MSG ( TEXTO , CADENA ) ;
        s = Nodo("SENT_ENVIAR_MENSAJE")
        s.hoja(self.consumir("ENV.MSG"))
        self.abrir(s)
        self.arg_texto_o_cadena(s, "DESTINATARIO")
        self.coma(s)
        self.arg_texto_o_cadena(s, "MENSAJE")
        self.cerrar(s)
        self.punto_coma(s)
        return s

    def sent_env_enl(self):
        s = Nodo("SENT_ENVIAR_ENLACE")
        s.hoja(self.consumir("ENV.ENL"))
        self.abrir(s)
        self.arg_texto_o_cadena(s, "DESTINATARIO")
        self.coma(s)
        self.arg_texto_o_cadena(s, "ENLACE")
        self.cerrar(s)
        self.punto_coma(s)
        return s

    def sent_ver_msg(self):
        s = Nodo("SENT_VER_MENSAJES")
        s.hoja(self.consumir("VER.MSG"))
        self.punto_coma(s)
        return s

    # ── Modularidad ───────────────────────────────────────────

    def sent_import(self):
        # IMPORT ( CADENA ) ;
        s = Nodo("SENT_IMPORTAR")
        s.hoja(self.consumir("IMPORT"))
        self.abrir(s)
        self.arg_texto_o_cadena(s, "ARCHIVO")
        self.cerrar(s)
        self.punto_coma(s)
        return s

    def sent_exportar(self):
        # EXPORTAR.TAR ( CADENA ) A ( CADENA ) ;
        s = Nodo("SENT_EXPORTAR")
        s.hoja(self.consumir("EXPORTAR.TAR"))
        self.abrir(s)
        self.arg_texto_o_cadena(s, "NOMBRE_TAREA")
        self.cerrar(s)
        if self.lexema() != "A":
            raise ErrorSintactico(f"Se esperaba A después de EXPORTAR.TAR(...) pero se encontró '{self.lexema()}'", self.linea_actual())
        d = Nodo("DESTINO")
        s.agregar(d)
        d.hoja(self.consumir("A"))
        self.abrir(d)
        self.arg_texto_o_cadena(d, "ARCHIVO")
        self.cerrar(d)
        self.punto_coma(s)
        return s

    def sent_usar_bib(self):
        s = Nodo("SENT_USAR_BIBLIOTECA")
        s.hoja(self.consumir("USAR.BIB"))
        self.abrir(s)
        self.arg_texto_o_cadena(s, "BIBLIOTECA")
        self.cerrar(s)
        self.punto_coma(s)
        return s


# ─────────────────────────────────────────────────────────────
# MAIN — prueba en consola
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    analizador = AnalizadorSintactico()

    print("Ingrese el código (línea vacía para terminar):\n")
    entrada = ""
    while True:
        linea = input()
        if linea == "":
            break
        entrada += linea + "\n"

    analizador.analizar(entrada)