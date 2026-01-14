from flask import Flask, render_template, request, jsonify
import backend
import json

app = Flask(__name__)

# Aseguramos que la DB exista al arrancar
backend.inicializar_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/quiz')
def get_quiz():
    # Obtiene 10 preguntas aleatorias
    datos = backend.obtener_examen_aleatorio(10)
    return jsonify(datos)

@app.route('/admin/importar', methods=['POST'])
def importar():
    try:
        # Recibe el JSON que te dio la IA y lo guarda
        data = request.json
        exito = backend.cargar_preguntas_desde_json(data)
        if exito:
            return jsonify({"status": "success", "message": "Preguntas guardadas"})
        else:
            return jsonify({"status": "error", "message": "Fallo al guardar"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)