from Lexico import AnalizadorLexico


class Nodo:

    def __init__(self, nombre):
        self.nombre = nombre
        self.hijos = []

    def agregar(self, nodo):
        self.hijos.append(nodo)

    def imprimir(self, nivel=0):
        print("│   " * nivel + "├── " + self.nombre)
        for hijo in self.hijos:
            hijo.imprimir(nivel + 1)


class AnalizadorSintactico:

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # =============================

    def actual(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def avanzar(self):
        self.pos += 1

    def consumir(self, esperado):

        token = self.actual()

        if token is None:
            raise Exception(
                f"Error sintáctico: se esperaba '{esperado}' y se encontró FIN"
            )

        lexema, tipo = token

        if lexema == esperado:
            self.avanzar()
            return Nodo(lexema)

        raise Exception(
            f"Error sintáctico: se esperaba '{esperado}' y se encontró '{lexema}'"
        )

    # =============================
    # PROGRAMA
    # =============================

    def programa(self):

        raiz = Nodo("PROGRAMA")

        while self.actual() is not None:
            raiz.agregar(self.sentencia())

        return raiz

    # =============================
    # SENTENCIA
    # =============================

    def sentencia(self):

        token = self.actual()

        if token is None:
            raise Exception("Error sintáctico inesperado")

        lexema, tipo = token

        if lexema == "CRE.USR":
            return self.crear_usuario()

        if lexema == "CRE.GRP":
            return self.crear_grupo()

        if lexema == "CRE.TAR":
            return self.crear_tarea()

        if lexema == "ASIG.USR":
            return self.asignar_usuario()

        if lexema.startswith("ROL."):
            return self.rol()

        # ===== NUEVAS SENTENCIAS (IDEA #4, #5, #6, #7) =====

        if lexema == "REC.TAR":
            return self.tarea_recurrente()

        if lexema == "ETIQ.TAR":
            return self.etiquetar_tarea()

        if lexema == "FILTRO.TAR":
            return self.filtrar_tareas()

        if lexema == "VER.VISTA":
            return self.ver_vista()

        if lexema == "NOTIF.CUANDO":
            return self.notificacion_cuando()

        if lexema == "NOTIF.RECORDAR":
            return self.notificacion_recordar()

        if lexema == "SUSCRIBIR":
            return self.suscribir()

        if lexema == "IMPORT":
            return self.importar()

        if lexema == "EXPORTAR.TAR":
            return self.exportar_tarea()

        if lexema == "USAR.BIB":
            return self.usar_biblioteca()

        raise Exception(
            f"Error sintáctico: sentencia no válida '{lexema}'"
        )

    # =============================
    # CRE.USR (original)
    # =============================

    def crear_usuario(self):

        nodo = Nodo("CREAR_USUARIO")

        nodo.agregar(self.consumir("CRE.USR"))
        nodo.agregar(self.consumir("("))

        nombre = self.texto_completo()
        nodo.agregar(Nodo(nombre))

        nodo.agregar(self.consumir(")"))
        nodo.agregar(self.consumir(";"))

        return nodo

    # =============================

    def crear_grupo(self):

        nodo = Nodo("CREAR_GRUPO")

        nodo.agregar(self.consumir("CRE.GRP"))
        nodo.agregar(self.consumir("("))

        nombre = self.texto_completo()
        nodo.agregar(Nodo(nombre))

        nodo.agregar(self.consumir(")"))
        nodo.agregar(self.consumir(";"))

        return nodo

    # =============================

    def crear_tarea(self):

        nodo = Nodo("CREAR_TAREA")

        nodo.agregar(self.consumir("CRE.TAR"))
        nodo.agregar(self.consumir("("))

        nombre = self.texto_completo()
        nodo.agregar(Nodo(nombre))

        nodo.agregar(self.consumir(")"))

        nodo.agregar(self.descripcion())
        nodo.agregar(self.fecha())
        nodo.agregar(self.prioridad())
        nodo.agregar(self.estado())

        nodo.agregar(self.consumir(";"))

        return nodo

    # =============================

    def descripcion(self):

        nodo = Nodo("DESCRIPCION")

        nodo.agregar(self.consumir("DES"))
        nodo.agregar(self.consumir("("))

        texto = self.texto_completo()
        nodo.agregar(Nodo(texto))

        nodo.agregar(self.consumir(")"))

        return nodo

    # =============================

    def fecha(self):

        nodo = Nodo("FECHA")

        nodo.agregar(self.consumir("FEC"))
        nodo.agregar(self.consumir("("))

        token = self.actual()

        if token is None:
            raise Exception(
                "Error sintáctico: se esperaba FECHA"
            )

        lexema, tipo = token

        # Permitir fechas normales O fechas inteligentes
        if tipo == "FECHA" or tipo == "FECHA_INTELIGENTE":
            nodo.agregar(Nodo(lexema))
            self.avanzar()
        else:
            raise Exception(
                f"Error sintáctico: se esperaba FECHA y se encontró '{lexema}'"
            )

        nodo.agregar(self.consumir(")"))

        return nodo

    # =============================

    def prioridad(self):

        token = self.actual()

        if token is None:
            raise Exception(
                "Error sintáctico: se esperaba PRIORIDAD"
            )

        lexema, tipo = token

        if not lexema.startswith("PRI."):
            raise Exception(
                f"Error sintáctico: se esperaba PRIORIDAD y se encontró '{lexema}'"
            )

        nodo = Nodo("PRIORIDAD")

        nodo.agregar(Nodo(lexema))

        self.avanzar()

        return nodo

    # =============================

    def estado(self):

        token = self.actual()

        if token is None:
            raise Exception(
                "Error sintáctico: se esperaba ESTADO"
            )

        lexema, tipo = token

        if not lexema.startswith("EST."):
            raise Exception(
                f"Error sintáctico: se esperaba ESTADO y se encontró '{lexema}'"
            )

        nodo = Nodo("ESTADO")

        nodo.agregar(Nodo(lexema))

        self.avanzar()

        return nodo

    # =============================

    def asignar_usuario(self):

        nodo = Nodo("ASIGNAR_USUARIO")

        nodo.agregar(self.consumir("ASIG.USR"))
        nodo.agregar(self.consumir("("))

        nombre1 = self.texto_completo()
        nodo.agregar(Nodo(nombre1))

        nodo.agregar(self.consumir(","))

        nombre2 = self.texto_completo()
        nodo.agregar(Nodo(nombre2))

        nodo.agregar(self.consumir(")"))
        nodo.agregar(self.consumir(";"))

        return nodo

    # =============================

    def rol(self):

        token = self.actual()

        lexema, tipo = token

        nodo = Nodo("ROL")

        nodo.agregar(Nodo(lexema))

        self.avanzar()

        nodo.agregar(self.consumir("("))

        nombre = self.texto_completo()
        nodo.agregar(Nodo(nombre))

        nodo.agregar(self.consumir(")"))
        nodo.agregar(self.consumir(";"))

        return nodo

    # =============================
    # TEXTO COMPLETO (original)
    # =============================

    def texto_completo(self):

        palabras = []

        while True:

            token = self.actual()

            if token is None:
                break

            lexema, tipo = token

            if lexema in [")", ",", ";"]:
                break

            palabras.append(lexema)

            self.avanzar()

        if not palabras:
            raise Exception(
                "Error sintáctico: se esperaba TEXTO"
            )

        return " ".join(palabras)

    # ==================================================
    # NUEVAS FUNCIONES (IDEA #4, #5, #6, #7)
    # ==================================================

    # ------------------------------
    # IDEA #4: FECHAS RECURRENTES
    # ------------------------------

    def tarea_recurrente(self):

        nodo = Nodo("TAREA_RECURRENTE")

        nodo.agregar(self.consumir("REC.TAR"))
        nodo.agregar(self.consumir("("))

        nombre = self.texto_completo()
        nodo.agregar(Nodo(nombre))

        nodo.agregar(self.consumir(")"))

        nodo.agregar(self.consumir("CADA"))

        token = self.actual()
        lexema, tipo = token
        if lexema not in ["SEMANA", "DIA"]:
            raise Exception("Error sintáctico: se esperaba SEMANA o DIA")
        nodo.agregar(Nodo(lexema))
        self.avanzar()

        nodo.agregar(self.consumir("A"))

        hora = self.texto_completo()
        nodo.agregar(Nodo(hora))

        nodo.agregar(self.consumir(";"))

        return nodo

    # ------------------------------
    # IDEA #5: ETIQUETAS Y FILTROS
    # ------------------------------

    def etiquetar_tarea(self):

        nodo = Nodo("ETIQUETAR_TAREA")

        nodo.agregar(self.consumir("ETIQ.TAR"))
        nodo.agregar(self.consumir("("))

        tarea = self.texto_completo()
        nodo.agregar(Nodo(tarea))

        nodo.agregar(self.consumir(")"))
        nodo.agregar(self.consumir("AGREGAR"))
        nodo.agregar(self.consumir("("))

        while True:
            etq = self.texto_completo()
            nodo.agregar(Nodo(etq))
            token = self.actual()
            if token and token[0] == ",":
                self.avanzar()
                continue
            break

        nodo.agregar(self.consumir(")"))
        nodo.agregar(self.consumir(";"))

        return nodo

    def filtrar_tareas(self):

        nodo = Nodo("FILTRAR_TAREAS")

        nodo.agregar(self.consumir("FILTRO.TAR"))
        nodo.agregar(self.consumir("("))

        condicion = []
        while True:
            token = self.actual()
            if token is None:
                break
            lexema, tipo = token
            if lexema == ")":
                break
            condicion.append(lexema)
            self.avanzar()

        nodo.agregar(Nodo(" ".join(condicion)))

        nodo.agregar(self.consumir(")"))
        nodo.agregar(self.consumir("→"))
        nodo.agregar(self.consumir("VISTA"))
        nodo.agregar(self.consumir("("))

        nombre_vista = self.texto_completo()
        nodo.agregar(Nodo(nombre_vista))

        nodo.agregar(self.consumir(")"))
        nodo.agregar(self.consumir(";"))

        return nodo

    def ver_vista(self):

        nodo = Nodo("VER_VISTA")

        nodo.agregar(self.consumir("VER.VISTA"))
        nodo.agregar(self.consumir("("))

        nombre = self.texto_completo()
        nodo.agregar(Nodo(nombre))

        nodo.agregar(self.consumir(")"))
        nodo.agregar(self.consumir(";"))

        return nodo

    # ------------------------------
    # IDEA #6: NOTIFICACIONES
    # ------------------------------

    def notificacion_cuando(self):

        nodo = Nodo("NOTIFICACION_CUANDO")

        nodo.agregar(self.consumir("NOTIF.CUANDO"))
        nodo.agregar(self.consumir("("))

        condicion = self.texto_completo()
        nodo.agregar(Nodo(condicion))

        nodo.agregar(self.consumir(")"))
        nodo.agregar(self.consumir("ENVIAR"))
        nodo.agregar(self.consumir("("))

        usuario = self.texto_completo()
        nodo.agregar(Nodo(usuario))

        nodo.agregar(self.consumir(")"))
        nodo.agregar(self.consumir(";"))

        return nodo

    def notificacion_recordar(self):

        nodo = Nodo("NOTIFICACION_RECORDAR")

        nodo.agregar(self.consumir("NOTIF.RECORDAR"))
        nodo.agregar(self.consumir("("))

        usuario = self.texto_completo()
        nodo.agregar(Nodo(usuario))

        nodo.agregar(self.consumir(","))

        fecha = self.texto_completo()
        nodo.agregar(Nodo(fecha))

        nodo.agregar(self.consumir(","))

        mensaje = self.texto_completo()
        nodo.agregar(Nodo(mensaje))

        nodo.agregar(self.consumir(")"))
        nodo.agregar(self.consumir(";"))

        return nodo

    def suscribir(self):

        nodo = Nodo("SUSCRIBIR")

        nodo.agregar(self.consumir("SUSCRIBIR"))
        nodo.agregar(self.consumir("("))

        usuario = self.texto_completo()
        nodo.agregar(Nodo(usuario))

        nodo.agregar(self.consumir(","))

        nodo.agregar(self.consumir("TAR"))
        nodo.agregar(self.consumir("("))

        tarea = self.texto_completo()
        nodo.agregar(Nodo(tarea))

        nodo.agregar(self.consumir(")"))
        nodo.agregar(self.consumir(")"))
        nodo.agregar(self.consumir(";"))

        return nodo

    # ------------------------------
    # IDEA #7: IMPORTACIÓN Y MODULARIDAD
    # ------------------------------

    def importar(self):

        nodo = Nodo("IMPORTAR")

        nodo.agregar(self.consumir("IMPORT"))
        nodo.agregar(self.consumir("("))

        archivo = self.texto_completo()
        nodo.agregar(Nodo(archivo))

        nodo.agregar(self.consumir(")"))
        nodo.agregar(self.consumir(";"))

        return nodo

    def exportar_tarea(self):

        nodo = Nodo("EXPORTAR_TAREA")

        nodo.agregar(self.consumir("EXPORTAR.TAR"))
        nodo.agregar(self.consumir("("))

        tarea = self.texto_completo()
        nodo.agregar(Nodo(tarea))

        nodo.agregar(self.consumir(")"))
        nodo.agregar(self.consumir("A"))
        nodo.agregar(self.consumir("("))

        archivo = self.texto_completo()
        nodo.agregar(Nodo(archivo))

        nodo.agregar(self.consumir(")"))
        nodo.agregar(self.consumir(";"))

        return nodo

    def usar_biblioteca(self):

        nodo = Nodo("USAR_BIBLIOTECA")

        nodo.agregar(self.consumir("USAR.BIB"))
        nodo.agregar(self.consumir("("))

        biblioteca = self.texto_completo()
        nodo.agregar(Nodo(biblioteca))

        nodo.agregar(self.consumir(")"))
        nodo.agregar(self.consumir(";"))

        return nodo


# =====================================
# MAIN
# =====================================

if __name__ == "__main__":

    analizador_lexico = AnalizadorLexico()

    print("Ingrese el codigo (Enter vacío para terminar):\n")

    entrada = ""

    while True:

        linea = input()

        if linea == "":
            break

        entrada += linea + " "

    tokens = analizador_lexico.analizar(entrada)

    print("\n🔹 TABLA DE TOKENS:\n")

    analizador_lexico.mostrar_tabla(tokens)

    print()

    try:

        sintactico = AnalizadorSintactico(tokens)

        arbol = sintactico.programa()

        print("✅ Cadena aceptada\n")

        print("🌳 Árbol sintáctico:\n")

        print("PROGRAMA")

        for hijo in arbol.hijos:
            hijo.imprimir(1)

    except Exception as e:

        print("\n❌", e)