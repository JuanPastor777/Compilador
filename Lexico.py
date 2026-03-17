import json
import re

class AnalizadorLexico:

    def __init__(self):
        try:
            with open("tokens.json", "r", encoding="utf-8") as f:
                self.tokens = json.load(f)
        except Exception as e:
            print("Error cargando tokens.json:", e)
            self.tokens = {}

    def analizar(self, texto):
        resultado = []

        #separar lexemas correctamente
        patron = r'[A-Za-z]+\.[A-Za-z]+\.[A-Za-z]+|[A-Za-z]+\.[A-Za-z]+|[A-Za-z_]\w*|\d+|\(|\)|,|;|-'
        lexemas = re.findall(patron, texto)

        for lex in lexemas:
            lex = lex.strip()
            tipo = self.clasificar(lex)
            resultado.append((lex, tipo))

        return resultado

    def clasificar(self, lex):

        # Palabras reservadas y simbolos
        if lex in self.tokens:
            return self.tokens[lex]

        # 2. Numeros 
        if lex.isdigit():
            return "NUMERO"

        # 3. Error lexico (empieza con número y tiene letras)
        if re.match(r'^\d+[a-zA-Z_]+', lex):
            return "ERROR_LEXICO"

        # 4. Identificador valido
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', lex):
            return "IDENTIFICADOR"

        # 5. Simbolos (respaldo)
        if lex in ['(', ')', ',', ';', '-']:
            return "SIMBOLO"

        # 6. Error general
        return "ERROR_LEXICO"

    def mostrar_tabla(self, tokens):
        print("\n{:<25} {:<20}".format("LEXEMA", "TIPO DE TOKEN"))
        print("-" * 45)
        for lex, tipo in tokens:
            print("{:<25} {:<20}".format(lex, tipo))


# ===== PROGRAMA PRINCIPAL =====

if __name__ == "__main__":

    analizador = AnalizadorLexico()

    print("Ingrese el codigo (Enter vacío para terminar):\n")

    entrada = ""
    while True:
        linea = input()
        if linea == "":
            break
        entrada += linea + " "

    tokens = analizador.analizar(entrada)

    analizador.mostrar_tabla(tokens)