from flask import Flask, render_template, request, jsonify
from Lexico import AnalizadorLexico
import json

app = Flask(__name__)
analizador = AnalizadorLexico()


with open('tokens.json', 'r', encoding='utf-8') as f:
    TOKENS_RESERVADOS = json.load(f)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analizar', methods=['POST'])
def analizar():
    codigo = request.json.get('codigo', '')


    tokens = analizador.analizar(codigo)


    resultado = []
    for lexema, tipo in tokens:
        resultado.append({
            'lexema': lexema,
            'tipo': tipo,
            'color': obtener_color(tipo)
        })


    tokens_unicos = len(set([t[0] for t in tokens]))
    variables = len([t for t in tokens if t[1] == 'IDENTIFICADOR'])


    conteo_tipos = {}
    for _, tipo in tokens:
        conteo_tipos[tipo] = conteo_tipos.get(tipo, 0) + 1

    return jsonify({
        'tokens': resultado,
        'estadisticas': {
            'errores': len([t for t in tokens if t[1] == 'ERROR_LEXICO' or t[1] == 'ERR_INV_DATE']),
            'advertencias': 0,
            'tokens_unicos': tokens_unicos,
            'variables': variables,
            'funciones': 0,
            'conteo_tipos': conteo_tipos
        }
    })


def obtener_color(tipo):
    """
    Asigna colores consistentes a cada tipo de token
    Paleta profesional basada en azules con acentos
    """
    colores = {
        # Azules (base del diseño)
        'PALABRA_RESERVADA': '#0a2472',  # Azul marino oscuro
        'IDENTIFICADOR': '#1e3a8a',  # Azul primario
        'DELIMITADOR': '#3b82f6',  # Azul claro

        # Verdes
        'NUMERO': '#22c55e',  # Verde esmeralda
        'FECHA': '#86efac',  # Verde claro

        # Neutros
        'TEXTO': '#475569',  # Gris pizarra

        # Acentos
        'SIMBOLO': '#f97316',  # Naranja

        # Errores
        'ERROR_LEXICO': '#ef4444',  # Rojo
        'ERR_INV_DATE': '#ef4444',  # Rojo
    }
    return colores.get(tipo, '#64748b')  # Gris por defecto


if __name__ == '__main__':
    app.run(debug=True)