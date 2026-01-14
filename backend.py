import sqlite3
import json

DB_NAME = "banco_preguntas.db"


def conectar_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = 1")
    conn.row_factory = sqlite3.Row  # Importante para acceder por nombre de columna
    return conn


def inicializar_db():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS materia (
            id_materia INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
    ''')

    # AGREGADO: columna 'pagina_referencia' y 'explicacion'
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pregunta (
            id_pregunta INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            explicacion TEXT,
            pagina_referencia INTEGER,
            id_materia INTEGER NOT NULL,
            FOREIGN KEY (id_materia) REFERENCES materia(id_materia)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS opciones (
            id_opcion INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            es_correcto INTEGER DEFAULT 0, 
            id_pregunta INTEGER NOT NULL,
            FOREIGN KEY (id_pregunta) REFERENCES pregunta(id_pregunta) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()


def cargar_preguntas_desde_json(json_data):
    """Recibe una lista de diccionarios (JSON) y los guarda en la BD."""
    conn = conectar_db()
    cursor = conn.cursor()

    try:
        for item in json_data:
            # 1. Gestionar Materia
            materia = item.get('materia', 'General')
            cursor.execute("INSERT OR IGNORE INTO materia (nombre) VALUES (?)", (materia,))
            cursor.execute("SELECT id_materia FROM materia WHERE nombre = ?", (materia,))
            id_materia = cursor.fetchone()['id_materia']

            # 2. Insertar Pregunta (con página y explicación)
            cursor.execute("""
                INSERT INTO pregunta (descripcion, explicacion, pagina_referencia, id_materia) 
                VALUES (?, ?, ?, ?)
            """, (item['pregunta'], item.get('explicacion', ''), item.get('pagina', 0), id_materia))

            id_pregunta = cursor.lastrowid

            # 3. Insertar Opciones
            for i, texto_opcion in enumerate(item['opciones']):
                es_correcta = 1 if i == item['indice_correcta'] else 0
                cursor.execute("INSERT INTO opciones (descripcion, es_correcto, id_pregunta) VALUES (?, ?, ?)",
                               (texto_opcion, es_correcta, id_pregunta))

        conn.commit()
        print(f"✅ Se importaron {len(json_data)} preguntas correctamente.")
        return True
    except Exception as e:
        conn.rollback()
        print(f"❌ Error importando JSON: {e}")
        return False
    finally:
        conn.close()


def obtener_examen_aleatorio(cantidad=10):
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM pregunta ORDER BY RANDOM() LIMIT ?", (cantidad,))
    preguntas_db = cursor.fetchall()

    examen = []
    for p in preguntas_db:
        cursor.execute("SELECT id_opcion, descripcion, es_correcto FROM opciones WHERE id_pregunta = ?",
                       (p['id_pregunta'],))
        opciones = cursor.fetchall()

        # Convertimos a diccionario para fácil uso en JS
        lista_opciones = []
        for op in opciones:
            lista_opciones.append({
                "id": op['id_opcion'],
                "texto": op['descripcion'],
                "es_correcta": bool(op['es_correcto'])
            })

        examen.append({
            "id": p['id_pregunta'],
            "pregunta": p['descripcion'],
            "explicacion": p['explicacion'],
            "pagina": p['pagina_referencia'],
            "opciones": lista_opciones
        })

    conn.close()
    return examen


if __name__ == "__main__":
    inicializar_db()