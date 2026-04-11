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

        raise Exception(
            f"Error sintáctico: sentencia no válida '{lexema}'"
        )

    # =============================
    # CRE.USR
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

        if tipo == "FECHA":
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
    # TEXTO COMPLETO
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


# =====================================
# MAIN DENTRO DEL SINTACTICO
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