from flask import Flask, render_template, request, jsonify
from Lexico import AnalizadorLexico
from Sintactico import AnalizadorSintactico
import json

app = Flask(__name__)
analizador_lexico = AnalizadorLexico()

with open('tokens.json', 'r', encoding='utf-8') as f:
    TOKENS_RESERVADOS = json.load(f)


@app.route('/')
def index():
    return render_template('index.html')


# ── Analizador Léxico ─────────────────────────────────────────

@app.route('/analizar', methods=['POST'])
def analizar():
    codigo = request.json.get('codigo', '')
    tokens = analizador_lexico.analizar(codigo)

    resultado = []
    for lexema, tipo in tokens:
        resultado.append({
            'lexema': lexema,
            'tipo': tipo,
            'color': obtener_color_lexico(tipo)
        })

    tokens_unicos = len(set([t[0] for t in tokens]))
    variables = len([t for t in tokens if t[1] == 'IDENTIFICADOR'])

    conteo_tipos = {}
    for _, tipo in tokens:
        conteo_tipos[tipo] = conteo_tipos.get(tipo, 0) + 1

    return jsonify({
        'tokens': resultado,
        'estadisticas': {
            'errores': len([t for t in tokens if t[1] in ('ERROR_LEXICO', 'ERR_INV_DATE', 'ERR_INV_TIME')]),
            'advertencias': 0,
            'tokens_unicos': tokens_unicos,
            'variables': variables,
            'funciones': 0,
            'conteo_tipos': conteo_tipos
        }
    })


# ── Analizador Sintáctico ─────────────────────────────────────

@app.route('/analizar-sintactico', methods=['POST'])
def analizar_sintactico():
    codigo = request.json.get('codigo', '')
    sint = AnalizadorSintactico()
    arbol, texto_arbol, exito, mensaje = sint.analizar(codigo)

    respuesta = {
        'exito': exito,
        'mensaje': mensaje,
        'texto_arbol': texto_arbol if exito else '',
        'arbol_json': arbol.a_dict() if exito else None,
    }

    if exito:
        respuesta['estadisticas'] = {
            'sentencias': len(arbol.hijos),
            'nodos_totales': contar_nodos(arbol),
            'profundidad': calcular_profundidad(arbol),
        }

    return jsonify(respuesta)


def contar_nodos(nodo):
    return 1 + sum(contar_nodos(h) for h in nodo.hijos)


def calcular_profundidad(nodo):
    if not nodo.hijos:
        return 0
    return 1 + max(calcular_profundidad(h) for h in nodo.hijos)


# ── Colores Léxico ────────────────────────────────────────────

def obtener_color_lexico(tipo):
    colores = {
        'PALABRA_RESERVADA': '#0a2472',
        'IDENTIFICADOR':     '#1e3a8a',
        'DELIMITADOR':       '#3b82f6',
        'NUMERO':            '#22c55e',
        'FECHA':             '#86efac',
        'EXPR_FECHA':        '#4ade80',
        'HORA':              '#a3e635',
        'CADENA':            '#e879f9',
        'OPERADOR_LOGICO':   '#f59e0b',
        'OPERADOR_COMPARACION': '#fb923c',
        'OPERADOR':          '#f97316',
        'TEXTO':             '#475569',
        'SIMBOLO':           '#f97316',
        'ERROR_LEXICO':      '#ef4444',
        'ERR_INV_DATE':      '#ef4444',
        'ERR_INV_TIME':      '#ef4444',
    }
    return colores.get(tipo, '#64748b')


if __name__ == '__main__':
    app.run(debug=True)