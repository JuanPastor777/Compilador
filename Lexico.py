import re
import json

class AnalizadorLexico:

    def __init__(self):

        # cargar palabras desde json
        with open("tokens.json", "r", encoding="utf-8") as f:
            config = json.load(f)

        self.palabras_reservadas = config["palabras_reservadas"]
        self.simbolos = config["simbolos"]
        self.errores = config["errores"]

    def analizar(self, codigo):

        tokens = []

        # separador de lexemas
        patron = r'[A-Z]+\.[A-Z]+(?:\.[A-Z]+)?|[A-Za-z_][A-Za-z0-9_]*|\d+|".*?"|[(),;\-]'
        lexemas = re.findall(patron, codigo)

        for lexema in lexemas:

            # palabras reservadas
            if lexema in self.palabras_reservadas:
                tokens.append((lexema, self.palabras_reservadas[lexema]))

            # símbolos
            elif lexema in self.simbolos:
                tokens.append((lexema, self.simbolos[lexema]))

            # identificadores
            elif re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_]*', lexema):
                tokens.append((lexema, "TOK_ID"))

            # números
            elif re.fullmatch(r'\d+', lexema):
                tokens.append((lexema, "TOK_NUM"))

            # texto libre
            elif lexema.startswith('"') and lexema.endswith('"'):
                tokens.append((lexema, "TOK_TEXT"))

            # error léxico
            else:
                tokens.append((lexema, "ERROR_LEXICO"))

        return tokens