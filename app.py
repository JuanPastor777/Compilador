from flask import Flask, render_template, request, jsonify
from Lexico import AnalizadorLexico
import json

app = Flask(__name__)
analizador = AnalizadorLexico()

# Cargar tokens reservados para colores
with open('tokens.json', 'r', encoding='utf-8') as f:
    TOKENS_RESERVADOS = json.load(f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analizar', methods=['POST'])
def analizar():
    codigo = request.json.get('codigo', '')
    
    # Usar tu analizador léxico existente
    tokens = analizador.analizar(codigo)
    
    # Preparar resultado con colores
    resultado = []
    for lexema, tipo in tokens:
        resultado.append({
            'lexema': lexema,
            'tipo': tipo,
            'color': obtener_color(tipo)
        })
    
    # Obtener estadísticas
    tokens_unicos = len(set([t[0] for t in tokens]))
    variables = len([t for t in tokens if t[1] == 'IDENTIFICADOR'])
    
    # Conteo por tipo
    conteo_tipos = {}
    for _, tipo in tokens:
        conteo_tipos[tipo] = conteo_tipos.get(tipo, 0) + 1
    
    return jsonify({
        'tokens': resultado,
        'estadisticas': {
            'errores': len([t for t in tokens if t[1] == 'ERROR_LEXICO']),
            'advertencias': 0,
            'tokens_unicos': tokens_unicos,
            'variables': variables,
            'funciones': 0,
            'conteo_tipos': conteo_tipos
        }
    })

def obtener_color(tipo):
    colores = {
        'PALABRA_RESERVADA': '#purple',
        'IDENTIFICADOR': '#blue',
        'NUMERO': '#green',
        'SIMBOLO': '#orange',
        'ERROR_LEXICO': '#red'
    }
    return colores.get(tipo, '#gray')

if __name__ == '__main__':
    app.run(debug=True)