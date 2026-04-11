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

        texto = texto.replace("(", " ( ").replace(")", " ) ") \
            .replace(",", " , ").replace(";", " ; ").replace("→", " → ")

        partes = [p for p in texto.split() if p.strip()]

        dentro_parentesis = False

        for parte in partes:

            if parte == "(":
                dentro_parentesis = True
                resultado.append((parte, self.tokens.get(parte, "DELIMITADOR")))
                continue

            if parte == ")":
                dentro_parentesis = False
                resultado.append((parte, self.tokens.get(parte, "DELIMITADOR")))
                continue

            tipo = self.clasificar(parte, dentro_parentesis)
            resultado.append((parte, tipo))

        return resultado

    def clasificar(self, lex, dentro_parentesis):
        lex = lex.strip()

        if not lex:
            return "ERROR_LEXICO"

        if lex in self.tokens:
            return self.tokens[lex]

        # FECHAS INTELIGENTES (IDEA #4)
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', lex):
            if self.fecha_valida(lex):
                return "FECHA"
            return "ERR_INV_DATE"

        if re.fullmatch(r'HOY\+\d+', lex):
            return "FECHA_INTELIGENTE"
        if re.fullmatch(r'PROX\.(LUN|MAR|MIE|JUE|VIE|SAB|DOM)', lex):
            return "FECHA_INTELIGENTE"
        if lex == "FIN.MES":
            return "FECHA_INTELIGENTE"

        # HORA para notificaciones (IDEA #6)
        if re.fullmatch(r'\d{2}:\d{2}', lex):
            return "HORA"

        if dentro_parentesis:
            return "TEXTO"

        if lex.isdigit():
            return "NUMERO"

        if re.fullmatch(r'[a-z][a-z0-9_]*', lex):
            return "IDENTIFICADOR"

        if re.fullmatch(r'[A-Za-zÁÉÍÓÚáéíóúñÑ]+', lex):
            return "TEXTO"

        if lex in ["(", ")", ",", ";", "-", "+", "→"]:
            if lex in [",", "-", "+", "→"]:
                return "SIMBOLO"
            return "DELIMITADOR"

        return "ERROR_LEXICO"

    def fecha_valida(self, fecha):
        try:
            anio, mes, dia = map(int, fecha.split("-"))
            if 1 <= mes <= 12 and 1 <= dia <= 31:
                dias_por_mes = [31, 29 if self.es_bisiesto(anio) else 28, 31, 30, 31, 30,
                                31, 31, 30, 31, 30, 31]
                return dia <= dias_por_mes[mes - 1]
            return False
        except:
            return False

    def es_bisiesto(self, anio):
        return anio % 4 == 0 and (anio % 100 != 0 or anio % 400 == 0)

    def mostrar_tabla(self, tokens):
        print("\n{:<30} {:<20}".format("LEXEMA", "TIPO DE TOKEN"))
        print("-" * 55)
        for lex, tipo in tokens:
            print("{:<30} {:<20}".format(lex, tipo))


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