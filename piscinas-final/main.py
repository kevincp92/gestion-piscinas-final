from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

# Función para conectar a la base de datos
def conectar_bd():
    conn = sqlite3.connect('piscinas.db')
    conn.row_factory = sqlite3.Row  # Permite acceder a las columnas por nombre
    return conn

# Crear las tablas en la base de datos si no existen
def crear_base_datos():
    conn = conectar_bd()
    cursor = conn.cursor()
    
    # Crear tabla para las piscinas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS piscinas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        direccion TEXT,
        nombre TEXT,
        tamano TEXT,
        tipo_tratamiento TEXT,
        metros_cubicos REAL,
        otros TEXT,
        orden INTEGER DEFAULT 0
    )
    ''')

    # Crear tabla para los mantenimientos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mantenimiento (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        piscina_id INTEGER,
        fecha_hora TEXT,
        barredora TEXT,
        pastillas_cloro INTEGER,
        alguicida TEXT,
        carbonato TEXT,
        floculante TEXT,
        choque TEXT,
        bicarbonato TEXT,
        acido TEXT,
        FOREIGN KEY (piscina_id) REFERENCES piscinas(id) ON DELETE CASCADE
    )
    ''')
    conn.commit()
    conn.close()

# Crear la base de datos al iniciar la aplicación
crear_base_datos()

# Página principal
@app.route('/')
def index():
    try:
        conn = conectar_bd()
        cursor = conn.execute("SELECT * FROM piscinas ORDER BY orden")
        piscinas = cursor.fetchall()
        total_piscinas = len(piscinas)
        conn.close()
        return render_template('index.html', piscinas=piscinas, total_piscinas=total_piscinas)
    except Exception as e:
        print(f"Error al cargar la página principal: {e}")
        return f"Hubo un error al cargar la página principal: {e}"

# Ruta para actualizar el orden de las piscinas
@app.route('/actualizar-orden', methods=['POST'])
def actualizar_orden():
    try:
        ordenes = request.get_json()
        conn = conectar_bd()
        for piscina_id, nuevo_orden in ordenes.items():
            conn.execute("UPDATE piscinas SET orden = ? WHERE id = ?", (nuevo_orden, piscina_id))
        conn.commit()
        conn.close()
        return '', 204  # No content
    except Exception as e:
        print(f"Error al actualizar el orden: {e}")
        return f"Hubo un error al actualizar el orden: {e}", 500

# Página para agregar una nueva piscina
@app.route('/agregar-piscina', methods=['GET', 'POST'])
def agregar_piscina():
    if request.method == 'POST':
        try:
            direccion = request.form['direccion']
            nombre = request.form['nombre']
            tamano = request.form.get('tamano', '')
            tipo_tratamiento = request.form.get('tipo_tratamiento', '')
            metros_cubicos = float(request.form.get('metros_cubicos', 0))
            otros = request.form.get('otros', '')

            conn = conectar_bd()
            max_orden = conn.execute("SELECT MAX(orden) FROM piscinas").fetchone()[0]
            nuevo_orden = (max_orden + 1) if max_orden is not None else 1

            conn.execute('''
                INSERT INTO piscinas (direccion, nombre, tamano, tipo_tratamiento, metros_cubicos, otros, orden)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (direccion, nombre, tamano, tipo_tratamiento, metros_cubicos, otros, nuevo_orden))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
        except Exception as e:
            print(f"Error al agregar la piscina: {e}")
            return f"Hubo un error al agregar la piscina: {e}"
    return render_template('agregar_piscina.html')

# Ruta para eliminar una piscina
@app.route('/eliminar-piscina/<int:piscina_id>', methods=['POST'])
def eliminar_piscina(piscina_id):
    try:
        conn = conectar_bd()
        # Eliminar los mantenimientos relacionados con la piscina
        conn.execute("DELETE FROM mantenimiento WHERE piscina_id = ?", (piscina_id,))
        # Eliminar la piscina
        conn.execute("DELETE FROM piscinas WHERE id = ?", (piscina_id,))
        conn.commit()
        conn.close()
        return '', 204  # No content
    except Exception as e:
        print(f"Error al eliminar la piscina: {e}")
        return f"Hubo un error al eliminar la piscina: {e}", 500

# Página para registrar mantenimiento de una piscina
@app.route('/registrar-mantenimiento/<int:piscina_id>', methods=['GET', 'POST'])
def registrar_mantenimiento(piscina_id):
    if request.method == 'POST':
        try:
            fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            barredora = request.form['barredora']
            pastillas_cloro = int(request.form.get('pastillas_cloro', '0') or 0)
            alguicida = request.form.get('alguicida', '')
            carbonato = request.form.get('carbonato', '')
            floculante = request.form.get('floculante', '')
            choque = request.form.get('choque', '')
            bicarbonato = request.form.get('bicarbonato', '')
            acido = request.form.get('acido', '')

            conn = conectar_bd()
            conn.execute('''
                INSERT INTO mantenimiento (piscina_id, fecha_hora, barredora, pastillas_cloro, alguicida, carbonato, floculante, choque, bicarbonato, acido)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (piscina_id, fecha_hora, barredora, pastillas_cloro, alguicida, carbonato, floculante, choque, bicarbonato, acido))
            conn.commit()
            conn.close()
            return redirect(url_for('detalle_piscina', piscina_id=piscina_id))
        except Exception as e:
            print(f"Error al registrar mantenimiento: {e}")
            return f"Hubo un error al registrar el mantenimiento: {e}"

    return render_template('registrar_mantenimiento.html', piscina_id=piscina_id)

# Página para ver el detalle de una piscina
@app.route('/piscina/<int:piscina_id>')
def detalle_piscina(piscina_id):
    try:
        conn = conectar_bd()
        piscina = conn.execute("SELECT * FROM piscinas WHERE id = ?", (piscina_id,)).fetchone()
        historial = conn.execute("SELECT * FROM mantenimiento WHERE piscina_id = ? ORDER BY fecha_hora DESC", (piscina_id,)).fetchall()
        conn.close()
        return render_template('detalle_piscina.html', piscina=piscina, historial=historial)
    except Exception as e:
        print(f"Error al obtener detalles de la piscina: {e}")
        return f"Hubo un error al obtener los detalles de la piscina: {e}"

# Página para editar la información de una piscina
@app.route('/editar-piscina/<int:piscina_id>', methods=['GET', 'POST'])
def editar_piscina(piscina_id):
    conn = conectar_bd()
    if request.method == 'POST':
        try:
            direccion = request.form['direccion']
            nombre = request.form['nombre']
            tamano = request.form['tamano']
            tipo_tratamiento = request.form['tipo_tratamiento']
            metros_cubicos = float(request.form['metros_cubicos'])
            otros = request.form['otros']

            conn.execute('''
                UPDATE piscinas 
                SET direccion = ?, nombre = ?, tamano = ?, tipo_tratamiento = ?, metros_cubicos = ?, otros = ? 
                WHERE id = ?
            ''', (direccion, nombre, tamano, tipo_tratamiento, metros_cubicos, otros, piscina_id))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
        except Exception as e:
            print(f"Error al actualizar la piscina: {e}")
            return f"Hubo un error al actualizar la piscina: {e}"

    piscina = conn.execute("SELECT * FROM piscinas WHERE id = ?", (piscina_id,)).fetchone()
    conn.close()
    return render_template('editar_piscina.html', piscina=piscina)

# Página para editar un mantenimiento existente
@app.route('/editar-mantenimiento/<int:mantenimiento_id>', methods=['GET', 'POST'])
def editar_mantenimiento(mantenimiento_id):
    try:
        conn = conectar_bd()
        if request.method == 'POST':
            barredora = request.form['barredora']
            pastillas_cloro = int(request.form.get('pastillas_cloro', '0') or 0)
            alguicida = request.form.get('alguicida', '')
            carbonato = request.form.get('carbonato', '')
            floculante = request.form.get('floculante', '')
            choque = request.form.get('choque', '')
            bicarbonato = request.form.get('bicarbonato', '')
            acido = request.form.get('acido', '')

            conn.execute('''
                UPDATE mantenimiento
                SET barredora = ?, pastillas_cloro = ?, alguicida = ?, carbonato = ?, floculante = ?, choque = ?, bicarbonato = ?, acido = ?
                WHERE id = ?
            ''', (barredora, pastillas_cloro, alguicida, carbonato, floculante, choque, bicarbonato, acido, mantenimiento_id))
            conn.commit()
            conn.close()
            piscina_id = request.form['piscina_id']
            return redirect(url_for('detalle_piscina', piscina_id=piscina_id))

        # Obtener los datos del mantenimiento
        mantenimiento = conn.execute("SELECT * FROM mantenimiento WHERE id = ?", (mantenimiento_id,)).fetchone()
        conn.close()
        return render_template('editar_mantenimiento.html', mantenimiento=mantenimiento)
    except Exception as e:
        print(f"Error al editar mantenimiento: {e}")
        return f"Hubo un error al editar el mantenimiento: {e}"

# Ejecutar la aplicación en el puerto 81
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=81)
